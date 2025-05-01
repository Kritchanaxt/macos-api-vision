from Cocoa import CIImage, CIFilter
from Foundation import NSNumber
from Quartz import CIVector
import objc
import math

def correct_perspective(image: CIImage, top_left, top_right, bottom_right, bottom_left):
    """
    Corrects the perspective and crops the image using CoreImage.

    Args:
        image: CIImage object from CoreImage
        top_left, top_right, bottom_right, bottom_left: Corner points of the
                                                      rectangle.
    Returns:
        CIImage: Perspective-corrected image.
    """
    try:
        # Create perspective correction filter
        filter = CIFilter.filterWithName_("CIPerspectiveCorrection")
        if filter is None:
            raise ValueError("Could not create CIPerspectiveCorrection filter")

        # Ensure points are CIVectors
        def ensure_ci_vector(point):
            if isinstance(point, CIVector):
                return point

            try:
                if hasattr(point, 'x') and hasattr(point, 'y'):
                    x = float(point.x)
                    y = float(point.y)
                    return CIVector.vectorWithX_Y_(x, y)
                elif hasattr(point, 'X') and hasattr(point, 'Y'):
                    x = float(point.X())
                    y = float(point.Y())
                    return CIVector.vectorWithX_Y_(x, y)
                elif isinstance(point, dict) and 'x' in point and 'y' in point:
                    x = float(point['x'])
                    y = float(point['y'])
                    return CIVector.vectorWithX_Y_(x, y)
                elif hasattr(point, '__len__') and len(point) >= 2:
                    x = float(point[0])
                    y = float(point[1])
                    return CIVector.vectorWithX_Y_(x, y)
                else:
                    raise TypeError(f"Unknown point type: {type(point)}")

            except Exception as e:
                raise ValueError(f"Could not convert point to CIVector: {type(point)} - {str(e)}")

        ci_top_left = ensure_ci_vector(top_left)
        ci_top_right = ensure_ci_vector(top_right)
        ci_bottom_right = ensure_ci_vector(bottom_right)
        ci_bottom_left = ensure_ci_vector(bottom_left)

        # Debug print
        print(f"Correcting with points: TL={ci_top_left.X()},{ci_top_left.Y()}, "
              f"TR={ci_top_right.X()},{ci_top_right.Y()}, "
              f"BR={ci_bottom_right.X()},{ci_bottom_right.Y()}, "
              f"BL={ci_bottom_left.X()},{ci_bottom_left.Y()}")

        # Check orientation before perspective correction
        orientation = detect_document_orientation(ci_top_left, ci_top_right, ci_bottom_right, ci_bottom_left)
        print(f"Detected document orientation: {orientation}")
        
        # For upside-down documents, reorder points before correction
        if orientation == "upside_down":
            print("Document is upside down, reordering points...")
            # Swap points: TL↔BR, TR↔BL
            ci_top_left, ci_bottom_right = ci_bottom_right, ci_top_left
            ci_top_right, ci_bottom_left = ci_bottom_left, ci_top_right
        elif orientation == "rotated_90_cw":
            print("Document is rotated 90° clockwise, reordering points...")
            # Rotate points counterclockwise: TL→BL→BR→TR→TL
            ci_top_left, ci_bottom_left, ci_bottom_right, ci_top_right = \
                ci_top_right, ci_top_left, ci_bottom_left, ci_bottom_right
        elif orientation == "rotated_90_ccw":
            print("Document is rotated 90° counterclockwise, reordering points...")
            # Rotate points clockwise: TL→TR→BR→BL→TL
            ci_top_left, ci_top_right, ci_bottom_right, ci_bottom_left = \
                ci_bottom_left, ci_top_left, ci_top_right, ci_bottom_right
            
        # Apply perspective correction
        filter.setValue_forKey_(image, "inputImage")
        filter.setValue_forKey_(ci_top_left, "inputTopLeft")
        filter.setValue_forKey_(ci_top_right, "inputTopRight")
        filter.setValue_forKey_(ci_bottom_right, "inputBottomRight")
        filter.setValue_forKey_(ci_bottom_left, "inputBottomLeft")

        # Get output image
        output_image = filter.valueForKey_("outputImage")
        if output_image is None:
            raise ValueError("CIPerspectiveCorrection filter failed to produce output")

        # Additional check for orientation: 
        # Since the perspective correction sometimes doesn't handle rotations correctly,
        # we'll add a specific check for orientation after the correction
        output_image = validate_and_correct_orientation(output_image)
        
        return output_image

    except Exception as e:
        print(f"Error correcting perspective: {str(e)}")
        raise

def detect_document_orientation(tl, tr, br, bl):
  
    # Calculate the width and height of top and bottom sides
    top_width = math.sqrt((tr.X() - tl.X())**2 + (tr.Y() - tl.Y())**2)
    bottom_width = math.sqrt((br.X() - bl.X())**2 + (br.Y() - bl.Y())**2)
    left_height = math.sqrt((bl.X() - tl.X())**2 + (bl.Y() - tl.Y())**2)
    right_height = math.sqrt((br.X() - tr.X())**2 + (br.Y() - tr.Y())**2)
    
    # Calculate average width and height
    avg_width = (top_width + bottom_width) / 2
    avg_height = (left_height + right_height) / 2
    
    # Check if document is in portrait or landscape
    is_portrait = avg_height > avg_width
    
    # Check top-bottom order by comparing Y coordinates
    # In Core Image coordinates (origin at top-left), top points should have smaller Y values
    top_points_above = ((tl.Y() < bl.Y()) and (tr.Y() < br.Y()))
    
    # Check left-right order by comparing X coordinates
    # Left points should have smaller X values than right points
    correct_horizontal_order = ((tl.X() < tr.X()) and (bl.X() < br.X()))
    
    if top_points_above and correct_horizontal_order:
        return "normal"
    elif not top_points_above and not correct_horizontal_order:
        return "upside_down"
    elif top_points_above and not correct_horizontal_order:
        return "rotated_90_ccw" if is_portrait else "rotated_90_cw"
    elif not top_points_above and correct_horizontal_order:
        return "rotated_90_cw" if is_portrait else "rotated_90_ccw"
    
    # Default fallback
    return "normal"

def validate_and_correct_orientation(image):
   
    width = image.extent().size.width
    height = image.extent().size.height
    
    is_landscape = width > height
    
    needs_rotation = False
    
    if is_landscape and (width / height > 1.3):
        needs_rotation = True
        print("Image appears to be in incorrect orientation based on dimensions")
    
    
    if needs_rotation:
        transform = CIFilter.filterWithName_("CIAffineTransform")
        if transform is not None:
            transform.setValue_forKey_(image, "inputImage")
            transform.setValue_forKey_(NSNumber.numberWithFloat_(-1.0), "inputScaleX")
            transform.setValue_forKey_(NSNumber.numberWithFloat_(-1.0), "inputScaleY")
            transform.setValue_forKey_(NSNumber.numberWithFloat_(width), "inputTranslateX")
            transform.setValue_forKey_(NSNumber.numberWithFloat_(height), "inputTranslateY")
            
            rotated_image = transform.valueForKey_("outputImage")
            if rotated_image is not None:
                print("Applied 180-degree rotation to correct orientation")
                return rotated_image
    
    return image

def apply_orientation_correction(image, orientation):
  
    if orientation == "normal":
        return image
    
    rotation_angles = {
        "upside_down": math.pi,  # 180 degrees
        "rotated_90_cw": -math.pi/2,  # -90 degrees
        "rotated_90_ccw": math.pi/2,  # 90 degrees
    }
    
    angle = rotation_angles.get(orientation, 0)
    
    if abs(angle) > 0.001:  

        width = image.extent().size.width
        height = image.extent().size.height
        
        if abs(angle - math.pi) < 0.01:  
            transform = CIFilter.filterWithName_("CIAffineTransform")
            if transform is not None:
                transform.setValue_forKey_(image, "inputImage")
                transform.setValue_forKey_(NSNumber.numberWithFloat_(-1.0), "inputScaleX")
                transform.setValue_forKey_(NSNumber.numberWithFloat_(-1.0), "inputScaleY")
                transform.setValue_forKey_(NSNumber.numberWithFloat_(width), "inputTranslateX")
                transform.setValue_forKey_(NSNumber.numberWithFloat_(height), "inputTranslateY")
                
                rotated_image = transform.valueForKey_("outputImage")
                if rotated_image is not None:
                    return rotated_image
        
        elif abs(angle - math.pi/2) < 0.01 or abs(angle + math.pi/2) < 0.01: 
            transform = CIFilter.filterWithName_("CIAffineTransform")
            if transform is not None:
                transform.setValue_forKey_(image, "inputImage")
                
                # For 90 degrees CCW (PI/2)
                if abs(angle - math.pi/2) < 0.01:
                    transform.setValue_forKey_(NSNumber.numberWithFloat_(0.0), "inputScaleX")
                    transform.setValue_forKey_(NSNumber.numberWithFloat_(1.0), "inputScaleY")
                    transform.setValue_forKey_(NSNumber.numberWithFloat_(1.0), "inputShearY")
                    transform.setValue_forKey_(NSNumber.numberWithFloat_(height), "inputTranslateX")
                
                # For 90 degrees CW (-PI/2)
                elif abs(angle + math.pi/2) < 0.01:
                    transform.setValue_forKey_(NSNumber.numberWithFloat_(0.0), "inputScaleX")
                    transform.setValue_forKey_(NSNumber.numberWithFloat_(1.0), "inputScaleY")
                    transform.setValue_forKey_(NSNumber.numberWithFloat_(-1.0), "inputShearY")
                    transform.setValue_forKey_(NSNumber.numberWithFloat_(width), "inputTranslateY")
                
                rotated_image = transform.valueForKey_("outputImage")
                if rotated_image is not None:
                    return rotated_image
    
    return image