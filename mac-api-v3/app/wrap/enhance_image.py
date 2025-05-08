from Cocoa import CIImage, CIFilter
from Foundation import NSNumber
import objc

def enhance_image(image: CIImage):
   
    if image is None:
        raise ValueError("Input image is None")
        
    try:
        enhanced_image = image
        
        # Sharpen image - try UnsharpMask first, fall back to SharpenLuminance
        unsharp = CIFilter.filterWithName_("CIUnsharpMask")
        if unsharp is not None:
            unsharp.setValue_forKey_(enhanced_image, "inputImage")
            unsharp.setValue_forKey_(NSNumber.numberWithFloat_(0.7), "inputRadius")     
            unsharp.setValue_forKey_(NSNumber.numberWithFloat_(0.7), "inputIntensity")  
            
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
        
        # Noise reduction
        noise_filter = CIFilter.filterWithName_("CINoiseReduction")
        if noise_filter is not None:
            noise_filter.setValue_forKey_(enhanced_image, "inputImage")
            noise_filter.setValue_forKey_(NSNumber.numberWithFloat_(0.02), "inputNoiseLevel")  
            noise_filter.setValue_forKey_(NSNumber.numberWithFloat_(0.65), "inputSharpness")  
            
            output = noise_filter.valueForKey_("outputImage")
            if output is not None:
                enhanced_image = output
        
        
        return enhanced_image
    
    except Exception as e:
        print(f"Error enhancing image: {str(e)}")
        return image