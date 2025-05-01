from Cocoa import CIImage, CIFilter

def enhance_image(image: CIImage):
    """
    ปรับปรุงภาพด้วยตัวกรอง sharpen
    Args:
        image: CIImage object จาก CoreImage
    Returns:
        CIImage: ภาพที่ปรับปรุงแล้ว
    """
    filter = CIFilter.filterWithName_("CISharpenLuminance")
    filter.setValue_forKey_(image, "inputImage")
    filter.setValue_forKey_(1.0, "inputSharpness")
    
    output_image = filter.outputImage()
    if output_image is None:
        raise ValueError("ไม่สามารถปรับปรุงภาพได้")
    
    return output_image