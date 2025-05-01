from Cocoa import CIImage, CIFilter
from Foundation import NSNumber
import objc

def enhance_image(image: CIImage):
    """
    ปรับปรุงภาพด้วยตัวกรอง CoreImage
    Args:
        image: CIImage object จาก CoreImage
    Returns:
        CIImage: ภาพที่ปรับปรุงแล้ว
    """
    if image is None:
        raise ValueError("Input image is None")
        
    try:
        # สร้าง filter chain กับการตรวจสอบ null ทุกขั้นตอน
        enhanced_image = image
        
        # 1. แก้ไขสีเพี้ยน: ปรับ Color Controls
        color_controls = CIFilter.filterWithName_("CIColorControls")
        if color_controls is not None:
            color_controls.setValue_forKey_(enhanced_image, "inputImage")
            color_controls.setValue_forKey_(NSNumber.numberWithFloat_(1.05), "inputSaturation")
            color_controls.setValue_forKey_(NSNumber.numberWithFloat_(0.02), "inputBrightness")
            color_controls.setValue_forKey_(NSNumber.numberWithFloat_(1.1), "inputContrast")
            
            output = color_controls.valueForKey_("outputImage")
            if output is not None:
                enhanced_image = output
        
        # 2. เพิ่มความคมชัดแบบ Unsharp Mask
        unsharp = CIFilter.filterWithName_("CIUnsharpMask")
        if unsharp is not None:
            unsharp.setValue_forKey_(enhanced_image, "inputImage")
            unsharp.setValue_forKey_(NSNumber.numberWithFloat_(0.6), "inputRadius")
            unsharp.setValue_forKey_(NSNumber.numberWithFloat_(0.7), "inputIntensity")
            
            output = unsharp.valueForKey_("outputImage")
            if output is not None:
                enhanced_image = output
        else:
            # ถ้าไม่มี UnsharpMask ใช้ SharpenLuminance แทน
            sharpen = CIFilter.filterWithName_("CISharpenLuminance")
            if sharpen is not None:
                sharpen.setValue_forKey_(enhanced_image, "inputImage")
                sharpen.setValue_forKey_(NSNumber.numberWithFloat_(0.5), "inputSharpness")
                
                output = sharpen.valueForKey_("outputImage")
                if output is not None:
                    enhanced_image = output
        
        # 3. ลดสัญญาณรบกวนเล็กน้อย
        noise_filter = CIFilter.filterWithName_("CINoiseReduction")
        if noise_filter is not None:
            noise_filter.setValue_forKey_(enhanced_image, "inputImage")
            noise_filter.setValue_forKey_(NSNumber.numberWithFloat_(0.02), "inputNoiseLevel")
            noise_filter.setValue_forKey_(NSNumber.numberWithFloat_(0.6), "inputSharpness")
            
            output = noise_filter.valueForKey_("outputImage")
            if output is not None:
                enhanced_image = output
        
        # 4. เพิ่มความสดใสแบบเป็นธรรมชาติ
        vibrance = CIFilter.filterWithName_("CIVibrance")
        if vibrance is not None:
            vibrance.setValue_forKey_(enhanced_image, "inputImage")
            vibrance.setValue_forKey_(NSNumber.numberWithFloat_(0.3), "inputAmount")
            
            output = vibrance.valueForKey_("outputImage")
            if output is not None:
                enhanced_image = output
        
        return enhanced_image
    
    except Exception as e:
        print(f"Error enhancing image: {str(e)}")
        # กรณีมีข้อผิดพลาด ส่งคืนภาพต้นฉบับ
        return image