from PIL import Image
import io
import Foundation
import Cocoa
import Quartz
import numpy as np

def convert_to_supported_format(image: Image.Image) -> Image.Image:

    if image.mode not in ('RGB', 'RGBA'):
        image = image.convert('RGB')
    
    
    max_dimension = 4000  
    width, height = image.size
    
    if width > max_dimension or height > max_dimension:
        scale_ratio = min(max_dimension / width, max_dimension / height)
        new_width = int(width * scale_ratio)
        new_height = int(height * scale_ratio)
        
        image = image.resize((new_width, new_height), Image.LANCZOS)
    
    return image

def pil_to_ci_image(pil_image: Image.Image) -> Cocoa.CIImage:
   
    if pil_image.mode not in ('RGB', 'RGBA'):
        pil_image = pil_image.convert('RGB')
    
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    image_data = buffer.getvalue()
    
    ns_data = Foundation.NSData.dataWithBytes_length_(image_data, len(image_data))
    
    ci_image = Cocoa.CIImage.imageWithData_(ns_data)
    
    if ci_image is not None:
        return ci_image
    
    buffer = io.BytesIO()
    pil_image.save(buffer, format="TIFF")
    image_data = buffer.getvalue()
    
    ns_data = Foundation.NSData.dataWithBytes_length_(image_data, len(image_data))
    
    ci_image = Cocoa.CIImage.imageWithData_(ns_data)
    
    if ci_image is not None:
        return ci_image
    
    ns_image = Cocoa.NSImage.alloc().initWithData_(ns_data)
    ci_image = Cocoa.CIImage.imageWithData_(ns_image.TIFFRepresentation())
    
    if ci_image is not None:
        return ci_image
    
    raise ValueError("Failed to convert PIL Image to CIImage")

def ci_to_pil_image(ci_image: Cocoa.CIImage) -> Image.Image:
  
    try:
        context = Cocoa.CIContext.contextWithOptions_(None)
        
        extent = ci_image.extent()
        width = int(extent.size.width)
        height = int(extent.size.height)
        
        cg_image = context.createCGImage_fromRect_(ci_image, extent)
        if cg_image is None:
            raise ValueError("Failed to create CGImage from CIImage")
        
        bitmapRep = Cocoa.NSBitmapImageRep.alloc().initWithCGImage_(cg_image)
        if bitmapRep is None:
            raise ValueError("Failed to create NSBitmapImageRep")
        
        png_data = bitmapRep.representationUsingType_properties_(Cocoa.NSPNGFileType, None)
        if png_data is None:
            raise ValueError("Failed to create PNG data")
        
        python_data = bytes(png_data)
        
        return Image.open(io.BytesIO(python_data))
    
    except Exception as e:
        try:
            print(f"Primary conversion method failed, trying fallback: {str(e)}")
            
            options = {
                Cocoa.kCIContextUseSoftwareRenderer: False
            }
            context = Cocoa.CIContext.contextWithOptions_(options)
            
            extent = ci_image.extent()
            
            cg_image = context.createCGImage_fromRect_(ci_image, extent)
            
            ns_image = Cocoa.NSImage.alloc().initWithCGImage_size_(
                cg_image, 
                Cocoa.NSMakeSize(extent.size.width, extent.size.height)
            )
            
            tiff_data = ns_image.TIFFRepresentation()
            
            return Image.open(io.BytesIO(bytes(tiff_data)))
            
        except Exception as nested_e:
            raise ValueError(f"All conversion methods failed: {str(nested_e)} (original error: {str(e)})")