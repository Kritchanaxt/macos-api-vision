from Vision import VNImageRequestHandler, VNDetectRectanglesRequest
from Cocoa import CIImage
from Quartz import CIVector
from Foundation import NSError
import objc

def detect_document_edges(image: CIImage):
 
    try:
        # Create the request handler
        handler = VNImageRequestHandler.alloc().initWithCIImage_options_(image, None)
        
        # Create the rectangle detection request with more lenient parameters
        request = VNDetectRectanglesRequest.alloc().init()
        request.setMinimumAspectRatio_(0.3)        # Lower min aspect ratio (more flexible)
        request.setMaximumAspectRatio_(3.0)        # Higher max aspect ratio (more flexible)
        request.setQuadratureTolerance_(15.0)      # More tolerance for non-right angles
        request.setMinimumSize_(0.15)              # Smaller minimum size (15% of image)
        request.setMaximumObservations_(5)         # Look for more rectangles
        
        # Perform the request - Fixed NSError handling
        error_ptr = objc.nil
        success = handler.performRequests_error_([request], objc.byref(error_ptr))
        
        if not success:
            if error_ptr is not objc.nil:
                print(f"Vision request failed: {error_ptr}")
            raise ValueError("Document edge detection failed")

        # Check results
        results = request.results()
        if results and len(results) > 0:
            best_observation = None
            highest_confidence = 0.0

            for observation in results:
                confidence = observation.confidence()
                print(f"Rectangle detected with confidence: {confidence}")
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_observation = observation

            if best_observation is None or highest_confidence < 0.3:  # Set minimum confidence threshold
                raise ValueError("Document edge detection failed")

            img_width = image.extent().size.width
            img_height = image.extent().size.height


            def vision_to_ci_point(point, width, height):
                # Transform the normalized Vision coordinates to CI pixel coordinates
                x = point.X() * width
                # Flip Y coordinate (1.0 - y) for Core Image coordinate system
                y = (1.0 - point.Y()) * height
                return CIVector.vectorWithX_Y_(x, y)

            # Get normalized coordinates from the Vision observation
            top_left = vision_to_ci_point(best_observation.topLeft(), img_width, img_height)
            top_right = vision_to_ci_point(best_observation.topRight(), img_width, img_height)
            bottom_right = vision_to_ci_point(best_observation.bottomRight(), img_width, img_height)
            bottom_left = vision_to_ci_point(best_observation.bottomLeft(), img_width, img_height)

            # Debug print for coordinates
            print(f"Document detection points: TL=({top_left.X()},{top_left.Y()}), " 
                  f"TR=({top_right.X()},{top_right.Y()}), "
                  f"BR=({bottom_right.X()},{bottom_right.Y()}), "
                  f"BL=({bottom_left.X()},{bottom_left.Y()})")
                  
            # Verify the points make a reasonable quadrilateral
            is_valid = validate_quadrilateral(top_left, top_right, bottom_right, bottom_left, img_width, img_height)
            
            if not is_valid:
                print("Warning: Detected quadrilateral seems incorrect, using default rectangle")
                return create_default_rectangle(img_width, img_height)

            # Make sure points are in clockwise order for perspective correction
            points = ensure_clockwise_order(top_left, top_right, bottom_right, bottom_left)
            
            return points

        else:
            raise ValueError("Document edges not found in the image")

    except Exception as e:
        print(f"Error detecting document edges: {str(e)}")
        # Use default rectangle on error
        if hasattr(image, 'extent') and callable(image.extent):
            return create_default_rectangle(image.extent().size.width, image.extent().size.height)
        else:
            print("Unable to get image dimensions, using fallback values")
            return create_default_rectangle(1000, 1000)  # Fallback dimensions

def ensure_clockwise_order(tl, tr, br, bl):

    # Calculate cross product to determine if points are in clockwise order
    def cross_product(p1, p2, p3):
        return (p2.X() - p1.X()) * (p3.Y() - p1.Y()) - (p2.Y() - p1.Y()) * (p3.X() - p1.X())
    
    # Check if the quadrilateral is in clockwise order
    cp = cross_product(tl, tr, br)
    
    if cp >= 0:  # Already clockwise or linear
        return (tl, tr, br, bl)
    else:  # Counter-clockwise, reverse the order
        print("Points are in counter-clockwise order, reversing...")
        return (tl, bl, br, tr)

def validate_quadrilateral(tl, tr, br, bl, img_width, img_height):

    # Helper to calculate distance between two points
    def distance(p1, p2):
        return ((p1.X() - p2.X())**2 + (p1.Y() - p2.Y())**2)**0.5
    
    # Check if points are within image bounds (with small margin)
    margin = 0.2  # Allow points to be slightly outside image (20%)
    for point in [tl, tr, br, bl]:
        if (point.X() < -margin * img_width or point.X() > img_width * (1 + margin) or
            point.Y() < -margin * img_height or point.Y() > img_height * (1 + margin)):
            print(f"Point {point.X()},{point.Y()} is outside image bounds")
            return False
    
    # Calculate side lengths
    top = distance(tl, tr)
    right = distance(tr, br)
    bottom = distance(br, bl)
    left = distance(bl, tl)
    
    # Calculate diagonal lengths
    diag1 = distance(tl, br)
    diag2 = distance(tr, bl)
    
    # Check if any side is extremely small compared to image dimensions
    min_side_ratio = 0.05  # 5% of image dimension is minimum acceptable side
    min_side_length = min(img_width, img_height) * min_side_ratio
    if min(top, right, bottom, left) < min_side_length:
        print(f"One side is too small: {min(top, right, bottom, left)} < {min_side_length}")
        return False
    
    # Check aspect ratio isn't extreme
    aspect_ratio_max = 8.0  # Allow more extreme aspect ratios (was 5.0)
    width_avg = (top + bottom) / 2
    height_avg = (left + right) / 2
    if max(width_avg / height_avg, height_avg / width_avg) > aspect_ratio_max:
        print(f"Aspect ratio is extreme: {max(width_avg / height_avg, height_avg / width_avg)}")
        return False
    
    # Check for extreme differences in opposite sides (parallelism)
    side_diff_ratio = 3.0  # Allow more variance (was 2.0)
    if max(top / bottom if bottom > 0 else 999, bottom / top if top > 0 else 999) > side_diff_ratio or \
       max(left / right if right > 0 else 999, right / left if left > 0 else 999) > side_diff_ratio:
        print("Opposite sides have extreme length differences")
        return False
    
    return True

def create_default_rectangle(img_width, img_height):

    margin = 0.05  # 5% margin
    top_left = CIVector.vectorWithX_Y_(img_width * margin, img_height * margin)
    top_right = CIVector.vectorWithX_Y_(img_width * (1 - margin), img_height * margin)
    bottom_right = CIVector.vectorWithX_Y_(img_width * (1 - margin), img_height * (1 - margin))
    bottom_left = CIVector.vectorWithX_Y_(img_width * margin, img_height * (1 - margin))
    
    print("Using default rectangle points")
    return top_left, top_right, bottom_right, bottom_left