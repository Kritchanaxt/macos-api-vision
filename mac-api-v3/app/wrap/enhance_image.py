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
        
        # 1. แก้ไขสีเพี้ยน: ปรับ Color Controls - ลดความเข้มลงเล็กน้อย
        color_controls = CIFilter.filterWithName_("CIColorControls")
        if color_controls is not None:
            color_controls.setValue_forKey_(enhanced_image, "inputImage")
            color_controls.setValue_forKey_(NSNumber.numberWithFloat_(1.02), "inputSaturation")  # ลดลงจาก 1.05
            color_controls.setValue_forKey_(NSNumber.numberWithFloat_(0.01), "inputBrightness")  # ลดลงจาก 0.02
            color_controls.setValue_forKey_(NSNumber.numberWithFloat_(1.05), "inputContrast")     # ลดลงจาก 1.1
            
            output = color_controls.valueForKey_("outputImage")
            if output is not None:
                enhanced_image = output
        
        # 2. เพิ่มความคมชัดแบบ Unsharp Mask (ปรับให้มีค่าน้อยลง)
        unsharp = CIFilter.filterWithName_("CIUnsharpMask")
        if unsharp is not None:
            unsharp.setValue_forKey_(enhanced_image, "inputImage")
            unsharp.setValue_forKey_(NSNumber.numberWithFloat_(0.6), "inputRadius")  # ลดลงจาก 0.8
            unsharp.setValue_forKey_(NSNumber.numberWithFloat_(0.8), "inputIntensity")  # ลดลงจาก 1.0
            
            output = unsharp.valueForKey_("outputImage")
            if output is not None:
                enhanced_image = output
        else:
            # ถ้าไม่มี UnsharpMask ใช้ SharpenLuminance แทน (ลดค่าลง)
            sharpen = CIFilter.filterWithName_("CISharpenLuminance")
            if sharpen is not None:
                sharpen.setValue_forKey_(enhanced_image, "inputImage")
                sharpen.setValue_forKey_(NSNumber.numberWithFloat_(0.6), "inputSharpness")  # ลดลงจาก 0.8
                
                output = sharpen.valueForKey_("outputImage")
                if output is not None:
                    enhanced_image = output
        
        # 3. ลดสัญญาณรบกวนเล็กน้อย (คงเดิม 0.01)
        noise_filter = CIFilter.filterWithName_("CINoiseReduction")
        if noise_filter is not None:
            noise_filter.setValue_forKey_(enhanced_image, "inputImage")
            noise_filter.setValue_forKey_(NSNumber.numberWithFloat_(0.01), "inputNoiseLevel")
            noise_filter.setValue_forKey_(NSNumber.numberWithFloat_(0.7), "inputSharpness")
            
            output = noise_filter.valueForKey_("outputImage")
            if output is not None:
                enhanced_image = output
        
        # 4. เพิ่มความสดใสแบบเป็นธรรมชาติ (ลดลงเล็กน้อย)
        vibrance = CIFilter.filterWithName_("CIVibrance")
        if vibrance is not None:
            vibrance.setValue_forKey_(enhanced_image, "inputImage")
            vibrance.setValue_forKey_(NSNumber.numberWithFloat_(0.3), "inputAmount")  # ลดลงจาก 0.4
            
            output = vibrance.valueForKey_("outputImage")
            if output is not None:
                enhanced_image = output
        
        return enhanced_image
    
    except Exception as e:
        print(f"Error enhancing image: {str(e)}")
        # กรณีมีข้อผิดพลาด ส่งคืนภาพต้นฉบับ
        return image