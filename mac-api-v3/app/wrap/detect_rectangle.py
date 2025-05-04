from Vision import VNImageRequestHandler, VNDetectRectanglesRequest
from Cocoa import CIImage
from Quartz import CIVector
from Foundation import NSError
import objc
import math

def detect_document_edges(image: CIImage):
  
    try:
        handler = VNImageRequestHandler.alloc().initWithCIImage_options_(image, None)
        
        request = VNDetectRectanglesRequest.alloc().init()
        request.setMinimumAspectRatio_(0.2)        # Lower to detect more rectangles
        request.setMaximumAspectRatio_(5.0)        # Higher to handle wide/tall documents
        request.setQuadratureTolerance_(20.0)      # More tolerance for skewed documents
        request.setMinimumSize_(0.1)               # Detect rectangles at least 10% of image size
        request.setMaximumObservations_(8)         # Look for more rectangles to find the best one
        
        error_ptr = objc.nil
        success = handler.performRequests_error_([request], objc.byref(error_ptr))
        
        if not success:
            if error_ptr is not objc.nil:
                print(f"Vision request failed: {error_ptr}")
            raise ValueError("Document edge detection failed")

        results = request.results()
        if results and len(results) > 0:
            print(f"Found {len(results)} rectangles")
            
            best_observation = find_best_rectangle(results, image)
            
            if best_observation is None:
                print("No reliable document rectangle found")
                raise ValueError("No reliable document rectangle detected")

            img_width = image.extent().size.width
            img_height = image.extent().size.height
            
            points = vision_to_ci_points(best_observation, img_width, img_height)
            top_left, top_right, bottom_right, bottom_left = points
            
            print(f"Document detection points: TL=({top_left.X()},{top_left.Y()}), " 
                  f"TR=({top_right.X()},{top_right.Y()}), "
                  f"BR=({bottom_right.X()},{bottom_right.Y()}), "
                  f"BL=({bottom_left.X()},{bottom_left.Y()})")
                  
            is_valid = validate_quadrilateral(top_left, top_right, bottom_right, bottom_left, img_width, img_height)
            
            if not is_valid:
                print("Warning: Detected quadrilateral seems incorrect, using default rectangle")
                return create_default_rectangle(img_width, img_height)

            points = ensure_clockwise_order(top_left, top_right, bottom_right, bottom_left)
            
            return points
        else:
            print("No rectangles detected")
            raise ValueError("Document edges not found in the image")

    except Exception as e:
        print(f"Error detecting document edges: {str(e)}")
        if hasattr(image, 'extent') and callable(image.extent):
            return create_default_rectangle(image.extent().size.width, image.extent().size.height)
        else:
            print("Unable to get image dimensions, using fallback values")
            return create_default_rectangle(1000, 1000)  # Fallback dimensions

def find_best_rectangle(observations, image):
    best_observation = None
    highest_score = 0.0
    
    img_width = image.extent().size.width
    img_height = image.extent().size.height
    img_area = img_width * img_height
    
    for observation in observations:
        confidence = observation.confidence()
        
        top_left = observation.topLeft()
        top_right = observation.topRight()
        bottom_right = observation.bottomRight()
        bottom_left = observation.bottomLeft()
        
        width = ((top_right.x - top_left.x) + (bottom_right.x - bottom_left.x)) / 2
        height = ((bottom_left.y - top_left.y) + (bottom_right.y - top_right.y)) / 2
        
        area = width * height
        
        center_x = (top_left.x + top_right.x + bottom_right.x + bottom_left.x) / 4
        center_y = (top_left.y + top_right.y + bottom_right.y + bottom_left.y) / 4
        
        dist_from_center = math.sqrt((center_x - 0.5)**2 + (center_y - 0.5)**2)
        
        # Calculate various scoring factors
        # 1. Confidence score from Vision
        confidence_score = confidence
        
        # 2. Size score - prefer larger rectangles
        size_score = area * 2  # Multiply by 2 to give more weight to larger rectangles
        
        # 3. Center score - prefer rectangles near the center of the image
        center_score = 1.0 - min(dist_from_center * 2, 0.8)  # Higher for rectangles closer to center
        
        # 4. Shape score - prefer rectangles with aspect ratios close to common document ratios
        # Common aspect ratios: 1.414 (A4), 1.5 (3:2), 1.33 (4:3), 1.77 (16:9)
        aspect = max(width, height) / min(width, height) if min(width, height) > 0 else 999
        shape_score = 0.0
        for target_ratio in [1.414, 1.5, 1.33, 1.77]:
            ratio_diff = abs(aspect - target_ratio)
            if ratio_diff < 0.5:  # Close to a common ratio
                shape_score = max(shape_score, 1.0 - ratio_diff)
        
        # Combine scores with weights
        combined_score = (
            confidence_score * 0.3 +  # Confidence from Vision
            size_score * 0.4 +        # Size of rectangle
            center_score * 0.2 +      # Proximity to center
            shape_score * 0.1         # Aspect ratio
        )
        
        print(f"Rectangle: confidence={confidence:.2f}, area={area:.4f}, center_dist={dist_from_center:.2f}, " +
              f"aspect={aspect:.2f}, score={combined_score:.4f}")
        
        if combined_score > highest_score:
            highest_score = combined_score
            best_observation = observation
    
    if best_observation:
        print(f"Selected best rectangle with score={highest_score:.4f}")
    
    return best_observation

def vision_to_ci_points(observation, img_width, img_height):
    def vision_to_ci_point(point, width, height):
        x = point.x * width
        y = (1.0 - point.y) * height  # Flip Y coordinate for CI coordinate system
        return CIVector.vectorWithX_Y_(x, y)

    # Get points from Vision observation
    top_left = vision_to_ci_point(observation.topLeft(), img_width, img_height)
    top_right = vision_to_ci_point(observation.topRight(), img_width, img_height)
    bottom_right = vision_to_ci_point(observation.bottomRight(), img_width, img_height)
    bottom_left = vision_to_ci_point(observation.bottomLeft(), img_width, img_height)
    
    return top_left, top_right, bottom_right, bottom_left

def ensure_clockwise_order(tl, tr, br, bl):
  
    def cross_product(p1, p2, p3):
        return (p2.X() - p1.X()) * (p3.Y() - p1.Y()) - (p2.Y() - p1.Y()) * (p3.X() - p1.X())
    
    cp = cross_product(tl, tr, br)
    
    if cp >= 0:  # Already clockwise or collinear
        print("Points are in clockwise order")
        return (tl, tr, br, bl)
    else:  # Counter-clockwise, reverse the order
        print("Points are in counter-clockwise order, reversing...")
        return (bl, tl, tr, br)  # This reverses the order to make it clockwise

def validate_quadrilateral(tl, tr, br, bl, img_width, img_height):
   
    def distance(p1, p2):
        return ((p1.X() - p2.X())**2 + (p1.Y() - p2.Y())**2)**0.5
    
    margin = 0.25  # Allow points to be slightly outside image (25%)
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
    
    # Check minimum side length
    min_side_ratio = 0.05  # Minimum acceptable side length as a ratio of image dimension
    min_side_length = min(img_width, img_height) * min_side_ratio
    
    if min(top, right, bottom, left) < min_side_length:
        print(f"One side is too small: {min(top, right, bottom, left)} < {min_side_length}")
        return False
    
    # Check for extreme aspect ratio
    aspect_ratio_max = 10.0  # Maximum acceptable aspect ratio
    width_avg = (top + bottom) / 2
    height_avg = (left + right) / 2
    
    if max(width_avg / height_avg if height_avg > 0 else 999, 
           height_avg / width_avg if width_avg > 0 else 999) > aspect_ratio_max:
        print(f"Aspect ratio is extreme")
        return False
    
    # Check for reasonable area
    area = calculate_quadrilateral_area(tl, tr, br, bl)
    min_area_ratio = 0.01  # Area should be at least 1% of image area
    min_area = img_width * img_height * min_area_ratio
    
    if area < min_area:
        print(f"Quadrilateral area is too small: {area} < {min_area}")
        return False
    
    return True

def calculate_quadrilateral_area(p1, p2, p3, p4):
    # Split into two triangles and calculate area
    def triangle_area(a, b, c):
        return 0.5 * abs((b.X() - a.X()) * (c.Y() - a.Y()) - (c.X() - a.X()) * (b.Y() - a.Y()))
    
    area1 = triangle_area(p1, p2, p3)
    area2 = triangle_area(p1, p3, p4)
    return area1 + area2

def create_default_rectangle(img_width, img_height):
  
    margin = 0.05  # 5% margin
    top_left = CIVector.vectorWithX_Y_(img_width * margin, img_height * margin)
    top_right = CIVector.vectorWithX_Y_(img_width * (1 - margin), img_height * margin)
    bottom_right = CIVector.vectorWithX_Y_(img_width * (1 - margin), img_height * (1 - margin))
    bottom_left = CIVector.vectorWithX_Y_(img_width * margin, img_height * (1 - margin))
    
    print("Using default rectangle points")
    print(f"Default rectangle: TL=({top_left.X()},{top_left.Y()}), " 
          f"TR=({top_right.X()},{top_right.Y()}), "
          f"BR=({bottom_right.X()},{bottom_right.Y()}), "
          f"BL=({bottom_left.X()},{bottom_left.Y()})")
          
    return top_left, top_right, bottom_right, bottom_left