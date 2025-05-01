from Cocoa import CIImage, CIFilter, NSObject
from Quartz import CIVector, CGAffineTransformMakeRotation, CGAffineTransformMakeScale, CGAffineTransformMakeTranslation, CGAffineTransformConcat
from Foundation import NSNumber, NSValue
import objc
import math
import numpy as np

def correct_perspective(image: CIImage, top_left, top_right, bottom_right, bottom_left):
    """
    Apply perspective correction to an image using CIPerspectiveCorrection.
    Points should be in clockwise order: top-left, top-right, bottom-right, bottom-left.
    
    Returns a corrected CIImage with proper orientation.
    """
    try:
        # Create perspective correction filter
        filter = CIFilter.filterWithName_("CIPerspectiveCorrection")
        if filter is None:
            raise ValueError("Could not create CIPerspectiveCorrection filter")

        # Ensure points are CIVectors
        top_left, top_right, bottom_right, bottom_left = ensure_ci_vectors(
            top_left, top_right, bottom_right, bottom_left
        )

        # Debug print
        print(f"Original points: TL={top_left.X()},{top_left.Y()}, "
              f"TR={top_right.X()},{top_right.Y()}, "
              f"BR={bottom_right.X()},{bottom_right.Y()}, "
              f"BL={bottom_left.X()},{bottom_left.Y()}")

        # Calculate image dimensions for reference
        original_width = image.extent().size.width
        original_height = image.extent().size.height
        
        # Analyze document orientation
        orientation, aspect_ratio = analyze_document_orientation(
            top_left, top_right, bottom_right, bottom_left
        )
        print(f"Detected document orientation: {orientation}, aspect ratio: {aspect_ratio:.2f}")
        
        # Calculate natural dimensions of the document from points
        rect_width, rect_height = compute_rectangle_dimensions(
            top_left, top_right, bottom_right, bottom_left
        )
        
        # Apply perspective correction
        filter.setValue_forKey_(image, "inputImage")
        filter.setValue_forKey_(top_left, "inputTopLeft")
        filter.setValue_forKey_(top_right, "inputTopRight")
        filter.setValue_forKey_(bottom_right, "inputBottomRight")
        filter.setValue_forKey_(bottom_left, "inputBottomLeft")

        # Get output image
        output_image = filter.valueForKey_("outputImage")
        if output_image is None:
            raise ValueError("CIPerspectiveCorrection filter failed to produce output")

        # Get resulting dimensions
        result_width = output_image.extent().size.width
        result_height = output_image.extent().size.height
        print(f"Resulting image dimensions: {result_width}x{result_height}")
            
        # Apply additional transformations to fix orientation if needed
        output_image = fix_output_orientation(output_image, orientation, rect_width, rect_height)
        
        # Double-check orientation based on aspect ratio and fix if needed
        output_image = check_and_fix_orientation(output_image, aspect_ratio)
            
        return output_image

    except Exception as e:
        print(f"Error correcting perspective: {str(e)}")
        raise

def ensure_ci_vectors(top_left, top_right, bottom_right, bottom_left):
    def to_ci_vector(point):
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

    return (to_ci_vector(top_left), to_ci_vector(top_right), 
            to_ci_vector(bottom_right), to_ci_vector(bottom_left))

def analyze_document_orientation(tl, tr, br, bl):
  
    # Calculate the width and height of sides
    top_width = math.sqrt((tr.X() - tl.X())**2 + (tr.Y() - tl.Y())**2)
    bottom_width = math.sqrt((br.X() - bl.X())**2 + (br.Y() - bl.Y())**2)
    left_height = math.sqrt((bl.X() - tl.X())**2 + (bl.Y() - tl.Y())**2)
    right_height = math.sqrt((br.X() - tr.X())**2 + (br.Y() - tr.Y())**2)
    
    # Calculate average width and height
    avg_width = (top_width + bottom_width) / 2
    avg_height = (left_height + right_height) / 2
    
    # Calculate aspect ratio (always greater than 1.0)
    aspect_ratio = max(avg_width, avg_height) / min(avg_width, avg_height) if min(avg_width, avg_height) > 0 else 1.0
    
    # Calculate angles of sides relative to horizontal/vertical
    try:
        top_angle = math.degrees(math.atan2(tr.Y() - tl.Y(), tr.X() - tl.X()))
        right_angle = math.degrees(math.atan2(br.Y() - tr.Y(), br.X() - tr.X()))
        bottom_angle = math.degrees(math.atan2(br.Y() - bl.Y(), br.X() - bl.X()))
        left_angle = math.degrees(math.atan2(bl.Y() - tl.Y(), bl.X() - tl.X()))
        
        # Normalize angles to 0-360 range
        angles = [angle % 360 for angle in [top_angle, right_angle, bottom_angle, left_angle]]
        
        # Calculate average horizontal and vertical angles
        horizontal_angle = (top_angle + bottom_angle) / 2
        vertical_angle = (right_angle + left_angle) / 2
        
        print(f"Angle analysis: Top={top_angle:.2f}°, Right={right_angle:.2f}°, Bottom={bottom_angle:.2f}°, Left={left_angle:.2f}°")
        print(f"Average angles: Horizontal={horizontal_angle:.2f}°, Vertical={vertical_angle:.2f}°")
        
    except Exception as e:
        print(f"Error calculating angles: {str(e)}")
        horizontal_angle = 0
        vertical_angle = 90
    
    # Method 1: Check if document is upside down by comparing top and bottom Y coordinates
    top_y_avg = (tl.Y() + tr.Y()) / 2
    bottom_y_avg = (bl.Y() + br.Y()) / 2
    y_orientation = "upside_down" if bottom_y_avg < top_y_avg else "normal"
    
    # Method 2: Check document orientation using diagonal directions
    # Calculate diagonals
    diag1 = (tr.X() - bl.X(), tr.Y() - bl.Y())  # top-right to bottom-left
    diag2 = (br.X() - tl.X(), br.Y() - tl.Y())  # bottom-right to top-left
    
    # Calculate diagonal directions
    diag1_angle = math.degrees(math.atan2(diag1[1], diag1[0])) % 360
    diag2_angle = math.degrees(math.atan2(diag2[1], diag2[0])) % 360
    
    print(f"Diagonal angles: Diag1={diag1_angle:.2f}°, Diag2={diag2_angle:.2f}°")
    
    # For normal orientation, diag1 should be roughly -45° and diag2 should be roughly 45°
    # For 90° CW, diag1 should be roughly -135° and diag2 should be roughly -45°
    # For 90° CCW, diag1 should be roughly 45° and diag2 should be roughly 135°
    # For 180° (upside down), diag1 should be roughly 135° and diag2 should be roughly -135°
    
    # Method 3: Check orientation using the width/height ratio and angles
    is_landscape = avg_width > avg_height
    
    # Determine if rotation is needed based on angles and aspect ratio
    if abs(horizontal_angle) < 45 and abs(vertical_angle - 90) < 45:
        # Normal orientation
        angle_orientation = "normal"
    elif abs(horizontal_angle - 90) < 45 and abs(vertical_angle) < 45:
        # 90 degrees clockwise or counter-clockwise
        if right_angle < 0:
            angle_orientation = "rotated_90_ccw"
        else:
            angle_orientation = "rotated_90_cw"
    elif abs(horizontal_angle - 180) < 45 and abs(vertical_angle - 270) < 45:
        # 180 degrees (upside down)
        angle_orientation = "upside_down"
    else:
        # Default to normal if we can't determine
        angle_orientation = "normal"
    
    # Combine the methods - prioritize the Y-coordinate method for upside_down detection
    if y_orientation == "upside_down":
        orientation = "upside_down"
    else:
        orientation = angle_orientation
    
    # Special case for landscape documents that need rotation
    if orientation == "normal" and is_landscape and aspect_ratio > 1.3:
        # If the document appears to be in landscape orientation but should be portrait,
        # we might need to rotate it 90 degrees
        orientation = "check_rotation"
    
    return orientation, aspect_ratio

def compute_rectangle_dimensions(tl, tr, br, bl):

    # Calculate the width (average of top and bottom sides)
    top_width = math.sqrt((tr.X() - tl.X())**2 + (tr.Y() - tl.Y())**2)
    bottom_width = math.sqrt((br.X() - bl.X())**2 + (br.Y() - bl.Y())**2)
    width = (top_width + bottom_width) / 2
    
    # Calculate the height (average of left and right sides)
    left_height = math.sqrt((bl.X() - tl.X())**2 + (bl.Y() - tl.Y())**2)
    right_height = math.sqrt((br.X() - tr.X())**2 + (br.Y() - tr.Y())**2)
    height = (left_height + right_height) / 2
    
    return width, height

def fix_output_orientation(image, orientation, rect_width, rect_height):
   
    try:
        # Get image dimensions
        img_width = image.extent().size.width
        img_height = image.extent().size.height
        
        # If the orientation is normal, just return the image as is
        if orientation == "normal":
            return image
            
        # Create transform filter
        transform = CIFilter.filterWithName_("CIAffineTransform")
        if transform is None:
            print("Warning: Could not create CIAffineTransform filter")
            return image
        
        # Apply transformations based on orientation
        corrected_image = image
        
        if orientation == "upside_down":
            # For upside-down: rotate 180 degrees
            print("Applying 180 degree rotation to fix upside down document")
            
            # Create a rotation transform (π radians = 180 degrees)
            rotation_transform = CGAffineTransformMakeRotation(math.pi)
            
            # Apply translation to keep the image in frame after rotation
            translation_transform = CGAffineTransformMakeTranslation(img_width, img_height)
            
            # Combine the transforms: first rotate, then translate
            combined_transform = CGAffineTransformConcat(rotation_transform, translation_transform)
            
            # Apply the transform - IMPORTANT: Set the entire transform at once
            transform.setValue_forKey_(corrected_image, "inputImage")
            transform.setValue_forKey_(NSValue.valueWithCGAffineTransform_(combined_transform), "inputTransform")
            
            output = transform.valueForKey_("outputImage")
            
            if output is not None:
                corrected_image = output
            else:
                print("Warning: Failed to apply rotation transform")
                
        elif orientation == "rotated_90_cw":
            # For 90 degrees clockwise: rotate -90 degrees
            print("Applying -90 degree rotation to fix document rotated 90° clockwise")
            
            # Create a rotation transform (-π/2 radians = -90 degrees)
            rotation_transform = CGAffineTransformMakeRotation(-math.pi/2)
            
            # Apply translation to keep image in frame after rotation
            translation_transform = CGAffineTransformMakeTranslation(0, img_width)
            
            # Combine the transforms
            combined_transform = CGAffineTransformConcat(rotation_transform, translation_transform)
            
            # Apply the combined transform - use NSValue to wrap the CGAffineTransform
            transform.setValue_forKey_(corrected_image, "inputImage")
            transform.setValue_forKey_(NSValue.valueWithCGAffineTransform_(combined_transform), "inputTransform")
            
            output = transform.valueForKey_("outputImage")
            
            if output is not None:
                corrected_image = output
            else:
                print("Warning: Failed to apply rotation transform")
                
        elif orientation == "rotated_90_ccw":
            # For 90 degrees counter-clockwise: rotate 90 degrees
            print("Applying 90 degree rotation to fix document rotated 90° counter-clockwise")
            
            # Create a rotation transform (π/2 radians = 90 degrees)
            rotation_transform = CGAffineTransformMakeRotation(math.pi/2)
            
            # Apply translation to keep image in frame after rotation
            translation_transform = CGAffineTransformMakeTranslation(img_height, 0)
            
            # Combine the transforms
            combined_transform = CGAffineTransformConcat(rotation_transform, translation_transform)
            
            # Apply the combined transform - use NSValue to wrap the CGAffineTransform
            transform.setValue_forKey_(corrected_image, "inputImage")
            transform.setValue_forKey_(NSValue.valueWithCGAffineTransform_(combined_transform), "inputTransform")
            
            output = transform.valueForKey_("outputImage")
            
            if output is not None:
                corrected_image = output
            else:
                print("Warning: Failed to apply rotation transform")
        
        elif orientation == "check_rotation":
            # For documents that may need rotation based on aspect ratio
            img_aspect = img_width / img_height if img_height > 0 else 1.0
            
            # If the resulting image is wider than tall and exceeds a threshold aspect ratio,
            # we may want to rotate it 90 degrees to get a portrait orientation
            if img_aspect > 1.3:  # Landscape orientation
                print("Applying 90 degree rotation to convert landscape to portrait")
                
                # Create a rotation transform (π/2 radians = 90 degrees)
                rotation_transform = CGAffineTransformMakeRotation(math.pi/2)
                
                # Apply translation to keep image in frame after rotation
                translation_transform = CGAffineTransformMakeTranslation(img_height, 0)
                
                # Combine the transforms
                combined_transform = CGAffineTransformConcat(rotation_transform, translation_transform)
                
                # Apply the combined transform properly as NSValue
                transform.setValue_forKey_(corrected_image, "inputImage")
                transform.setValue_forKey_(NSValue.valueWithCGAffineTransform_(combined_transform), "inputTransform")
                
                output = transform.valueForKey_("outputImage")
                
                if output is not None:
                    corrected_image = output
                else:
                    print("Warning: Failed to apply rotation transform")
        
        return corrected_image
        
    except Exception as e:
        print(f"Error fixing orientation: {str(e)}")
        return image
    
def check_and_fix_orientation(image, original_aspect_ratio):

    try:
        # Get image dimensions
        img_width = image.extent().size.width
        img_height = image.extent().size.height
        img_aspect = img_width / img_height if img_height > 0 else 1.0
        
        print(f"Final image aspect ratio: {img_aspect:.2f}, Original aspect ratio: {original_aspect_ratio:.2f}")
        
        # Check if the aspect ratio suggests we need to rotate
        # Common aspect ratios to check against:
        # - A4 paper: 1.414 (portrait) or 0.707 (landscape)
        # - ID cards: ~1.59 (portrait) or ~0.63 (landscape)
        # - US Letter: 1.294 (portrait) or 0.773 (landscape)
        common_ratios = [1.414, 1.59, 1.294]  # Portrait orientations
        
        # Create transform filter if needed
        transform = None
        need_rotation = False
        
        # Check if current aspect ratio significantly differs from original or common ratios
        # If the image is in portrait but should be landscape or vice versa
        if (img_aspect < 1.0 and original_aspect_ratio > 1.3) or (img_aspect > 1.3 and original_aspect_ratio < 1.0):
            # The image orientation likely doesn't match what it should be
            need_rotation = True
        else:
            # Check against common document aspect ratios
            for ratio in common_ratios:
                if abs(img_aspect - ratio) < 0.1:  # Close to portrait
                    need_rotation = False
                    break
                elif abs(img_aspect - (1/ratio)) < 0.1:  # Close to landscape
                    # For many document types, portrait is preferred
                    need_rotation = True
                    break
        
        if need_rotation:
            print("Applying additional 90 degree rotation to fix orientation based on aspect ratio")
            
            # Create transform filter if not already created
            if transform is None:
                transform = CIFilter.filterWithName_("CIAffineTransform")
                if transform is None:
                    print("Warning: Could not create CIAffineTransform filter")
                    return image
            
            # Create a rotation transform (π/2 radians = 90 degrees)
            rotation_transform = CGAffineTransformMakeRotation(math.pi/2)
            
            # Apply translation to keep image in frame after rotation
            translation_transform = CGAffineTransformMakeTranslation(img_height, 0)
            
            # Combine the transforms
            combined_transform = CGAffineTransformConcat(rotation_transform, translation_transform)
            
            # Apply the combined transform properly as NSValue
            transform.setValue_forKey_(image, "inputImage")
            transform.setValue_forKey_(NSValue.valueWithCGAffineTransform_(combined_transform), "inputTransform")
            
            output = transform.valueForKey_("outputImage")
            
            if output is not None:
                return output
            else:
                print("Warning: Failed to apply aspect ratio correction transform")
        
        return image
        
    except Exception as e:
        print(f"Error in check_and_fix_orientation: {str(e)}")
        return image