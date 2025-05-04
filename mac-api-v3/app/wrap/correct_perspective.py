from Cocoa import CIImage, CIFilter, NSObject
from Quartz import CIVector, CGAffineTransformMakeRotation, CGAffineTransformMakeScale, CGAffineTransformMakeTranslation, CGAffineTransformConcat
from Foundation import NSNumber, NSValue
import objc
import math
import numpy as np

def correct_perspective(image: CIImage, top_left, top_right, bottom_right, bottom_left):

    try:
        filter = CIFilter.filterWithName_("CIPerspectiveCorrection")
        if filter is None:
            raise ValueError("Could not create CIPerspectiveCorrection filter")

        top_left, top_right, bottom_right, bottom_left = ensure_ci_vectors(
            top_left, top_right, bottom_right, bottom_left
        )

        print(f"Original points: TL={top_left.X()},{top_left.Y()}, "
              f"TR={top_right.X()},{top_right.Y()}, "
              f"BR={bottom_right.X()},{bottom_right.Y()}, "
              f"BL={bottom_left.X()},{bottom_left.Y()}")

        original_width = image.extent().size.width
        original_height = image.extent().size.height
        
        orientation, aspect_ratio = analyze_document_orientation(
            top_left, top_right, bottom_right, bottom_left
        )
        print(f"Detected document orientation: {orientation}, aspect ratio: {aspect_ratio:.2f}")
        
        rect_width, rect_height = compute_rectangle_dimensions(
            top_left, top_right, bottom_right, bottom_left
        )
        
        filter.setValue_forKey_(image, "inputImage")
        filter.setValue_forKey_(top_left, "inputTopLeft")
        filter.setValue_forKey_(top_right, "inputTopRight")
        filter.setValue_forKey_(bottom_right, "inputBottomRight")
        filter.setValue_forKey_(bottom_left, "inputBottomLeft")

        output_image = filter.valueForKey_("outputImage")
        if output_image is None:
            raise ValueError("CIPerspectiveCorrection filter failed to produce output")

        result_width = output_image.extent().size.width
        result_height = output_image.extent().size.height
        print(f"Resulting image dimensions: {result_width}x{result_height}")
            
        output_image = fix_output_orientation(output_image, orientation, rect_width, rect_height)
        
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
  
    top_width = math.sqrt((tr.X() - tl.X())**2 + (tr.Y() - tl.Y())**2)
    bottom_width = math.sqrt((br.X() - bl.X())**2 + (br.Y() - bl.Y())**2)
    left_height = math.sqrt((bl.X() - tl.X())**2 + (bl.Y() - tl.Y())**2)
    right_height = math.sqrt((br.X() - tr.X())**2 + (br.Y() - tr.Y())**2)
    
    avg_width = (top_width + bottom_width) / 2
    avg_height = (left_height + right_height) / 2
    
    aspect_ratio = max(avg_width, avg_height) / min(avg_width, avg_height) if min(avg_width, avg_height) > 0 else 1.0
    
    try:
        top_angle = math.degrees(math.atan2(tr.Y() - tl.Y(), tr.X() - tl.X()))
        right_angle = math.degrees(math.atan2(br.Y() - tr.Y(), br.X() - tr.X()))
        bottom_angle = math.degrees(math.atan2(br.Y() - bl.Y(), br.X() - bl.X()))
        left_angle = math.degrees(math.atan2(bl.Y() - tl.Y(), bl.X() - tl.X()))
        
        angles = [angle % 360 for angle in [top_angle, right_angle, bottom_angle, left_angle]]
        
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
    diag1 = (tr.X() - bl.X(), tr.Y() - bl.Y())  # top-right to bottom-left
    diag2 = (br.X() - tl.X(), br.Y() - tl.Y())  # bottom-right to top-left
    
    diag1_angle = math.degrees(math.atan2(diag1[1], diag1[0])) % 360
    diag2_angle = math.degrees(math.atan2(diag2[1], diag2[0])) % 360
    
    print(f"Diagonal angles: Diag1={diag1_angle:.2f}°, Diag2={diag2_angle:.2f}°")
    
    # Method 3: Check orientation using the width/height ratio and angles
    is_landscape = avg_width > avg_height
    
    if abs(horizontal_angle) < 45 and abs(vertical_angle - 90) < 45:
        angle_orientation = "normal"
    elif abs(horizontal_angle - 90) < 45 and abs(vertical_angle) < 45:
        if right_angle < 0:
            angle_orientation = "rotated_90_ccw"
        else:
            angle_orientation = "rotated_90_cw"
    elif abs(horizontal_angle - 180) < 45 and abs(vertical_angle - 270) < 45:
        angle_orientation = "upside_down"
    else:
        angle_orientation = "normal"
    
    if y_orientation == "upside_down":
        orientation = "upside_down"
    else:
        orientation = angle_orientation
    
    if orientation == "normal" and is_landscape and aspect_ratio > 1.3:
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
        img_width = image.extent().size.width
        img_height = image.extent().size.height
        
        if orientation == "normal":
            return image
            
        transform = CIFilter.filterWithName_("CIAffineTransform")
        if transform is None:
            print("Warning: Could not create CIAffineTransform filter")
            return image
        
        corrected_image = image
        
        if orientation == "upside_down":
            print("Applying 180 degree rotation to fix upside down document")
            
            rotation_transform = CGAffineTransformMakeRotation(math.pi)
            
            translation_transform = CGAffineTransformMakeTranslation(img_width, img_height)
            
            combined_transform = CGAffineTransformConcat(rotation_transform, translation_transform)
            
            transform.setValue_forKey_(corrected_image, "inputImage")
            transform.setValue_forKey_(NSValue.valueWithCGAffineTransform_(combined_transform), "inputTransform")
            
            output = transform.valueForKey_("outputImage")
            
            if output is not None:
                corrected_image = output
            else:
                print("Warning: Failed to apply rotation transform")
                
        elif orientation == "rotated_90_cw":
            print("Applying -90 degree rotation to fix document rotated 90° clockwise")
            
            rotation_transform = CGAffineTransformMakeRotation(-math.pi/2)
            
            translation_transform = CGAffineTransformMakeTranslation(0, img_width)
            
            combined_transform = CGAffineTransformConcat(rotation_transform, translation_transform)
            
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
            img_aspect = img_width / img_height if img_height > 0 else 1.0
            
            if img_aspect > 1.3:  # Landscape orientation
                print("Applying 90 degree rotation to convert landscape to portrait")
                
                rotation_transform = CGAffineTransformMakeRotation(math.pi/2)
                
                translation_transform = CGAffineTransformMakeTranslation(img_height, 0)
                
                combined_transform = CGAffineTransformConcat(rotation_transform, translation_transform)
                
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
        img_width = image.extent().size.width
        img_height = image.extent().size.height
        img_aspect = img_width / img_height if img_height > 0 else 1.0
        
        print(f"Final image aspect ratio: {img_aspect:.2f}, Original aspect ratio: {original_aspect_ratio:.2f}")
        
        common_ratios = [1.414, 1.59, 1.294]  # Portrait orientations
        
        transform = None
        need_rotation = False
        
        if (img_aspect < 1.0 and original_aspect_ratio > 1.3) or (img_aspect > 1.3 and original_aspect_ratio < 1.0):
            need_rotation = True
        else:
            for ratio in common_ratios:
                if abs(img_aspect - ratio) < 0.1:  # Close to portrait
                    need_rotation = False
                    break
                elif abs(img_aspect - (1/ratio)) < 0.1:  # Close to landscape
                    need_rotation = True
                    break
        
        if need_rotation:
            print("Applying additional 90 degree rotation to fix orientation based on aspect ratio")
            
            if transform is None:
                transform = CIFilter.filterWithName_("CIAffineTransform")
                if transform is None:
                    print("Warning: Could not create CIAffineTransform filter")
                    return image
            
            rotation_transform = CGAffineTransformMakeRotation(math.pi/2)
            
            translation_transform = CGAffineTransformMakeTranslation(img_height, 0)
            
            combined_transform = CGAffineTransformConcat(rotation_transform, translation_transform)
            
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