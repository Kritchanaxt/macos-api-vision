from Cocoa import CIImage, CIFilter
from Foundation import NSNumber
import objc

def enhance_image(image: CIImage):
   
    if image is None:
        raise ValueError("Input image is None")
        
    try:
        enhanced_image = image
        
        # Step 1: Exposure adjustment
        exposure_adjust = CIFilter.filterWithName_("CIExposureAdjust")
        if exposure_adjust is not None:
            exposure_adjust.setValue_forKey_(enhanced_image, "inputImage")
            exposure_adjust.setValue_forKey_(NSNumber.numberWithFloat_(0.1), "inputEV")  # Slightly increase exposure
            
            output = exposure_adjust.valueForKey_("outputImage")
            if output is not None:
                enhanced_image = output
        
        # Step 2: Color controls (saturation, brightness, contrast)
        color_controls = CIFilter.filterWithName_("CIColorControls")
        if color_controls is not None:
            color_controls.setValue_forKey_(enhanced_image, "inputImage")
            color_controls.setValue_forKey_(NSNumber.numberWithFloat_(1.05), "inputSaturation")  # Slight saturation boost
            color_controls.setValue_forKey_(NSNumber.numberWithFloat_(0.02), "inputBrightness")  # Slight brightness boost
            color_controls.setValue_forKey_(NSNumber.numberWithFloat_(1.08), "inputContrast")    # Improve contrast
            
            output = color_controls.valueForKey_("outputImage")
            if output is not None:
                enhanced_image = output
        
        # Step 3: Sharpen image - try UnsharpMask first, fall back to SharpenLuminance
        unsharp = CIFilter.filterWithName_("CIUnsharpMask")
        if unsharp is not None:
            unsharp.setValue_forKey_(enhanced_image, "inputImage")
            unsharp.setValue_forKey_(NSNumber.numberWithFloat_(0.7), "inputRadius")     # Medium radius
            unsharp.setValue_forKey_(NSNumber.numberWithFloat_(0.7), "inputIntensity")  # Moderate intensity
            
            output = unsharp.valueForKey_("outputImage")
            if output is not None:
                enhanced_image = output
        else:
            sharpen = CIFilter.filterWithName_("CISharpenLuminance")
            if sharpen is not None:
                sharpen.setValue_forKey_(enhanced_image, "inputImage")
                sharpen.setValue_forKey_(NSNumber.numberWithFloat_(0.6), "inputSharpness")
                
                output = sharpen.valueForKey_("outputImage")
                if output is not None:
                    enhanced_image = output
        
        # Step 4: Noise reduction
        noise_filter = CIFilter.filterWithName_("CINoiseReduction")
        if noise_filter is not None:
            noise_filter.setValue_forKey_(enhanced_image, "inputImage")
            noise_filter.setValue_forKey_(NSNumber.numberWithFloat_(0.02), "inputNoiseLevel")  # Slightly stronger
            noise_filter.setValue_forKey_(NSNumber.numberWithFloat_(0.65), "inputSharpness")   # Balance with sharpness
            
            output = noise_filter.valueForKey_("outputImage")
            if output is not None:
                enhanced_image = output
        
        # Step 5: Highlight and shadow adjustment
        highlight_shadow = CIFilter.filterWithName_("CIHighlightShadowAdjust")
        if highlight_shadow is not None:
            highlight_shadow.setValue_forKey_(enhanced_image, "inputImage")
            highlight_shadow.setValue_forKey_(NSNumber.numberWithFloat_(0.3), "inputHighlightAmount")  # Reduce highlights
            highlight_shadow.setValue_forKey_(NSNumber.numberWithFloat_(0.25), "inputShadowAmount")    # Open up shadows
            
            output = highlight_shadow.valueForKey_("outputImage")
            if output is not None:
                enhanced_image = output
        
        return enhanced_image
    
    except Exception as e:
        print(f"Error enhancing image: {str(e)}")
        return image