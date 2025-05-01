from PIL import Image
import io
import Foundation
import Cocoa
import Quartz
import objc

def convert_to_supported_format(image: Image.Image) -> Image.Image:
    """
    Convert image to a format supported by Vision/CoreImage
    
    Args:
        image: PIL Image
        
    Returns:
        Processed PIL Image
    """
    # Convert to RGB or RGBA to ensure compatibility with Vision Framework
    if image.mode not in ('RGB', 'RGBA'):
        image = image.convert('RGB')
    
    # Check image size and resize if too large
    max_dimension = 4000  # Maximum recommended size (pixels)
    width, height = image.size
    
    if width > max_dimension or height > max_dimension:
        # Calculate resize ratio
        scale_ratio = min(max_dimension / width, max_dimension / height)
        new_width = int(width * scale_ratio)
        new_height = int(height * scale_ratio)
        
        # Resize image
        image = image.resize((new_width, new_height), Image.LANCZOS)
    
    return image

def pil_to_ci_image(pil_image: Image.Image) -> Cocoa.CIImage:
    """
    Convert PIL Image to CIImage
    
    Args:
        pil_image: PIL Image
        
    Returns:
        CIImage object
    """
    # Convert PIL Image to PNG data
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    image_data = buffer.getvalue()
    
    # Convert to NSData
    ns_data = Foundation.NSData.dataWithBytes_length_(image_data, len(image_data))
    
    # Create CIImage from NSData
    ci_image = Cocoa.CIImage.imageWithData_(ns_data)
    if ci_image is None:
        raise ValueError("Failed to convert PIL Image to CIImage")
    
    return ci_image

def ci_to_pil_image(ci_image: Cocoa.CIImage) -> Image.Image:
    """
    Convert CIImage to PIL Image
    
    Args:
        ci_image: CIImage object
        
    Returns:
        PIL Image
    """
    import numpy as np
    
    try:
        # Create CIContext
        context = Cocoa.CIContext.contextWithOptions_(None)
        
        # Get the extent of the image
        extent = ci_image.extent()
        width = int(extent.size.width)
        height = int(extent.size.height)
        
        # Create CGImage from CIImage
        cg_image = context.createCGImage_fromRect_(ci_image, extent)
        if cg_image is None:
            raise ValueError("Failed to create CGImage from CIImage")
        
        # Create bitmap context
        colorspace = Quartz.CGColorSpaceCreateDeviceRGB()
        bitmap_info = Quartz.kCGImageAlphaPremultipliedFirst | Quartz.kCGBitmapByteOrder32Little
        
        # Create bitmap context
        bitmap_context = Quartz.CGBitmapContextCreate(
            None, width, height, 8, 4 * width, colorspace, bitmap_info
        )
        
        if bitmap_context is None:
            raise ValueError("Failed to create bitmap context")
        
        # Draw CGImage to bitmap context
        Quartz.CGContextDrawImage(bitmap_context, Quartz.CGRectMake(0, 0, width, height), cg_image)
        
        # Get image data from context
        cg_image_result = Quartz.CGBitmapContextCreateImage(bitmap_context)
        
        if cg_image_result is None:
            raise ValueError("Failed to create CGImage from bitmap context")
        
        # Get image data
        provider = Quartz.CGImageGetDataProvider(cg_image_result)
        data_provider = Quartz.CGDataProviderCopyData(provider)
        
        # Convert to numpy array
        buffer = np.frombuffer(data_provider, dtype=np.uint8)
        
        # Reshape to image dimensions
        buffer = buffer.reshape((height, width, 4))
        
        # Create PIL Image
        return Image.fromarray(buffer, mode="RGBA")
    
    except Exception as e:
        print(f"Error converting CIImage to PIL Image: {str(e)}")
        raise ValueError(f"Failed to convert CIImage to PIL Image: {str(e)}")