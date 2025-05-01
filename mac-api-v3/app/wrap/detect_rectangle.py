from Vision import VNImageRequestHandler, VNDetectRectanglesRequest
from Cocoa import CIImage
from Quartz import CIVector
import objc
from Foundation import NSError

def detect_document_edges(image: CIImage):
    """
    Detects document edges in an image using Vision Framework.

    Args:
        image: CIImage object from CoreImage
    Returns:
        tuple: 4 corner points of the rectangle (top_left, top_right,
               bottom_right, bottom_left) as CIVectors
    """
    try:
        # Create the request handler
        handler = VNImageRequestHandler.alloc().initWithCIImage_options_(image, None)
        
        # Create the rectangle detection request
        request = VNDetectRectanglesRequest.alloc().init()
        request.setMinimumAspectRatio_(0.5)  # Min aspect ratio (width/height)
        request.setMaximumAspectRatio_(2.0)  # Max aspect ratio
        request.setQuadratureTolerance_(12.0)  # Tolerance for right angles (degrees)
        request.setMinimumSize_(0.2)  # Minimum rectangle size as a fraction of the image size
        
        # Perform the request
        error = objc.allocateBuffer(1, NSError)
        success = handler.performRequests_error_([request], error)
        
        if not success:
            error = error[0]
            if error:
                print(f"Vision request failed: {error}")
            raise ValueError("การตรวจจับขอบเอกสารล้มเหลว")

        # Check results
        results = request.results()
        if results and len(results) > 0:
            # Select the result with highest confidence
            best_observation = None
            highest_confidence = 0.0

            for observation in results:
                confidence = observation.confidence()
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_observation = observation

            if best_observation is None:
                raise ValueError("ไม่พบขอบเอกสารที่มีความเชื่อมั่นเพียงพอ")

            img_width = image.extent().size.width
            img_height = image.extent().size.height

            # IMPORTANT: Vision and Core Image have different coordinate systems
            # Vision uses a coordinate system with origin at the bottom-left
            # Core Image uses a coordinate system with origin at the top-left
            # We need to transform Vision coordinates to Core Image coordinates

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
            # This helps catch cases where the detection might be incorrect
            is_valid = validate_quadrilateral(top_left, top_right, bottom_right, bottom_left, img_width, img_height)
            
            if not is_valid:
                print("Warning: Detected quadrilateral seems incorrect, using default rectangle")
                return create_default_rectangle(img_width, img_height)

            return top_left, top_right, bottom_right, bottom_left

        else:
            raise ValueError("ไม่พบขอบเอกสารในภาพ")

    except Exception as e:
        print(f"Error detecting document edges: {str(e)}")
        # Use default rectangle on error
        return create_default_rectangle(image.extent().size.width, image.extent().size.height)

def validate_quadrilateral(tl, tr, br, bl, img_width, img_height):
    """
    Validates that the detected points form a reasonable quadrilateral.
    
    Args:
        tl, tr, br, bl: The four corner points
        img_width, img_height: Image dimensions
        
    Returns:
        bool: True if the quadrilateral seems valid, False otherwise
    """
    # Helper to calculate distance between two points
    def distance(p1, p2):
        return ((p1.X() - p2.X())**2 + (p1.Y() - p2.Y())**2)**0.5
    
    # Check if points are within image bounds (with small margin)
    margin = 0.1
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
    min_side_ratio = 0.1
    min_side_length = min(img_width, img_height) * min_side_ratio
    if min(top, right, bottom, left) < min_side_length:
        print(f"One side is too small: {min(top, right, bottom, left)} < {min_side_length}")
        return False
    
    # Check aspect ratio isn't extreme
    aspect_ratio_max = 5.0
    width_avg = (top + bottom) / 2
    height_avg = (left + right) / 2
    if max(width_avg / height_avg, height_avg / width_avg) > aspect_ratio_max:
        print(f"Aspect ratio is extreme: {max(width_avg / height_avg, height_avg / width_avg)}")
        return False
    
    # Check for extreme differences in opposite sides (parallelism)
    side_diff_ratio = 2.0
    if max(top / bottom, bottom / top) > side_diff_ratio or max(left / right, right / left) > side_diff_ratio:
        print("Opposite sides have extreme length differences")
        return False
    
    return True

def create_default_rectangle(img_width, img_height):
    """
    Creates a default rectangle with margins around the image edges.
    
    Args:
        img_width, img_height: Image dimensions
        
    Returns:
        tuple: The four corner points of the default rectangle
    """
    margin = 0.05  # 5% margin
    top_left = CIVector.vectorWithX_Y_(img_width * margin, img_height * margin)
    top_right = CIVector.vectorWithX_Y_(img_width * (1 - margin), img_height * margin)
    bottom_right = CIVector.vectorWithX_Y_(img_width * (1 - margin), img_height * (1 - margin))
    bottom_left = CIVector.vectorWithX_Y_(img_width * margin, img_height * (1 - margin))
    
    print("Using default rectangle points")
    return top_left, top_right, bottom_right, bottom_left