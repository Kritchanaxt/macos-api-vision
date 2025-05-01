from Cocoa import CIImage, CIFilter
from Foundation import NSPoint, NSDictionary

def correct_perspective(image: CIImage, top_left: NSPoint, top_right: NSPoint, bottom_right: NSPoint, bottom_left: NSPoint):
    """
    ปรับเปอร์สเปคทีฟและครอบตัดภาพด้วย CoreImage
    Args:
        image: CIImage object จาก CoreImage
        top_left, top_right, bottom_right, bottom_left: จุดมุมของสี่เหลี่ยม
    Returns:
        CIImage: ภาพที่ปรับเปอร์สเปคทีฟแล้ว
    """
    filter = CIFilter.filterWithName_("CIPerspectiveCorrection")
    filter.setValue_forKey_(image, "inputImage")
    filter.setValue_forKey_(top_left, "inputTopLeft")
    filter.setValue_forKey_(top_right, "inputTopRight")
    filter.setValue_forKey_(bottom_right, "inputBottomRight")
    filter.setValue_forKey_(bottom_left, "inputBottomLeft")
    
    output_image = filter.outputImage()
    if output_image is None:
        raise ValueError("ไม่สามารถปรับเปอร์สเปคทีฟได้")
    
    return output_image