from Cocoa import CIImage, CIFilter
from Foundation import NSValue
import objc
import Quartz

def correct_perspective(image: CIImage, top_left, top_right, bottom_right, bottom_left):
    """
    ปรับเปอร์สเปคทีฟและครอบตัดภาพด้วย CoreImage
    Args:
        image: CIImage object จาก CoreImage
        top_left, top_right, bottom_right, bottom_left: จุดมุมของสี่เหลี่ยม
    Returns:
        CIImage: ภาพที่ปรับเปอร์สเปคทีฟแล้ว
    """
    try:
        # Create perspective correction filter
        filter = CIFilter.filterWithName_("CIPerspectiveCorrection")
        if filter is None:
            raise ValueError("ไม่สามารถสร้าง CIPerspectiveCorrection filter ได้")
        
        # Convert NSPoint to CIVector if needed - CoreImage uses lowercase properties
        # Let's ensure we have CGPoint/NSPoint objects with correct case properties
        # Some versions might use x/y (lower) and others X/Y (upper)
        
        # Create CGPoint parameters consistently (always using lowercase)
        try:
            # Create CIVectors from point coordinates
            from Quartz import CIVector
            ci_top_left = CIVector.vectorWithX_Y_(float(getattr(top_left, 'x', None) or top_left.X()), 
                                                float(getattr(top_left, 'y', None) or top_left.Y()))
            ci_top_right = CIVector.vectorWithX_Y_(float(getattr(top_right, 'x', None) or top_right.X()), 
                                                 float(getattr(top_right, 'y', None) or top_right.Y()))
            ci_bottom_right = CIVector.vectorWithX_Y_(float(getattr(bottom_right, 'x', None) or bottom_right.X()), 
                                                    float(getattr(bottom_right, 'y', None) or bottom_right.Y()))
            ci_bottom_left = CIVector.vectorWithX_Y_(float(getattr(bottom_left, 'x', None) or bottom_left.X()), 
                                                   float(getattr(bottom_left, 'y', None) or bottom_left.Y()))
            
            # Set input values using CIVectors (which ensures proper formatting)
            filter.setValue_forKey_(image, "inputImage")
            filter.setValue_forKey_(ci_top_left, "inputTopLeft")
            filter.setValue_forKey_(ci_top_right, "inputTopRight")
            filter.setValue_forKey_(ci_bottom_right, "inputBottomRight")
            filter.setValue_forKey_(ci_bottom_left, "inputBottomLeft")
        except Exception as e:
            # Fallback to trying direct point properties (if CIVector fails)
            print(f"Warning: Using fallback point conversion method: {str(e)}")
            filter.setValue_forKey_(image, "inputImage")
            filter.setValue_forKey_(top_left, "inputTopLeft")
            filter.setValue_forKey_(top_right, "inputTopRight")
            filter.setValue_forKey_(bottom_right, "inputBottomRight")
            filter.setValue_forKey_(bottom_left, "inputBottomLeft")
        
        # Get output image
        output_image = filter.valueForKey_("outputImage")
        if output_image is None:
            raise ValueError("ไม่สามารถปรับเปอร์สเปคทีฟได้")
        
        return output_image
    except Exception as e:
        print(f"Error in perspective correction: {str(e)}")
        raise ValueError(f"ไม่สามารถปรับเปอร์สเปคทีฟ: {str(e)}")