from Cocoa import CIImage, CIFilter
from Foundation import NSNumber
import objc

def enhance_image(image: CIImage):
    """
    ปรับปรุงภาพด้วยตัวกรอง sharpen
    Args:
        image: CIImage object จาก CoreImage
    Returns:
        CIImage: ภาพที่ปรับปรุงแล้ว
    """
    try:
        # Create sharpen filter
        filter = CIFilter.filterWithName_("CISharpenLuminance")
        if filter is None:
            raise ValueError("ไม่สามารถสร้าง CISharpenLuminance filter ได้")
        
        # Set input values
        filter.setValue_forKey_(image, "inputImage")
        filter.setValue_forKey_(NSNumber.numberWithFloat_(1.0), "inputSharpness")
        
        # Get output image
        output_image = filter.valueForKey_("outputImage")
        if output_image is None:
            raise ValueError("ไม่สามารถปรับปรุงภาพได้")
        
        return output_image
    except Exception as e:
        print(f"Error enhancing image: {str(e)}")
        # Return original image if enhancement fails
        return image