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
        # This detects if the document is upside down or rotated incorrectly
        orientation = detect_document_orientation(ci_top_left, ci_top_right, ci_bottom_right, ci_bottom_left)
        
        # Apply perspective correction
        # Set filter parameters
        filter.setValue_forKey_(image, "inputImage")
        filter.setValue_forKey_(ci_top_left, "inputTopLeft")
        filter.setValue_forKey_(ci_top_right, "inputTopRight")
        filter.setValue_forKey_(ci_bottom_right, "inputBottomRight")
        filter.setValue_forKey_(ci_bottom_left, "inputBottomLeft")

        # Get output image
        output_image = filter.valueForKey_("outputImage")
        if output_image is None:
            raise ValueError("CIPerspectiveCorrection filter failed to produce output")

        # Apply rotation based on detected orientation
        if orientation != "normal":
            print(f"Detected orientation: {orientation}, applying correction...")
            output_image = apply_orientation_correction(output_image, orientation)

        return output_image

    except Exception as e:
        print(f"Error correcting perspective: {str(e)}")
        raise

def detect_document_orientation(tl, tr, br, bl):
    """
    Detect the orientation of the document based on its corners.
    
    Args:
        tl, tr, br, bl: The corner points as CIVectors
    
    Returns:
        str: Orientation type - "normal", "upside_down", "rotated_90_cw", "rotated_90_ccw"
    """
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
        # If we're in this condition, it likely means the document is rotated 90° CCW
        return "rotated_90_ccw" if is_portrait else "rotated_90_cw"
    elif not top_points_above and correct_horizontal_order:
        # If we're in this condition, it likely means the document is rotated 90° CW
        return "rotated_90_cw" if is_portrait else "rotated_90_ccw"
    
    # Default fallback
    return "normal"

def apply_orientation_correction(image, orientation):
    """
    Apply rotation to correct image orientation.
    
    Args:
        image: CIImage to correct
        orientation: The detected orientation
        
    Returns:
        CIImage: Corrected image
    """
    if orientation == "normal":
        return image
    
    # Map orientation to rotation angle (in radians for CIStraightenFilter)
    rotation_angles = {
        "upside_down": math.pi,  # 180 degrees
        "rotated_90_cw": -math.pi/2,  # -90 degrees
        "rotated_90_ccw": math.pi/2,  # 90 degrees
    }
    
    angle = rotation_angles.get(orientation, 0)
    
    if abs(angle) > 0.001:  # Only rotate if angle is not close to zero
        rotation_filter = CIFilter.filterWithName_("CIStraightenFilter")
        if rotation_filter is not None:
            rotation_filter.setValue_forKey_(image, "inputImage")
            rotation_filter.setValue_forKey_(NSNumber.numberWithFloat_(angle), "inputAngle")
            rotated_image = rotation_filter.valueForKey_("outputImage")
            if rotated_image is not None:
                return rotated_image
    
    # Return original if rotation fails
    return image