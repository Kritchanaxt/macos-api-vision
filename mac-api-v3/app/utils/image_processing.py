from PIL import Image
import io
import Foundation
import Cocoa
import Quartz
import numpy as np

def convert_to_supported_format(image: Image.Image) -> Image.Image:
    """
    แปลงภาพให้เป็นรูปแบบที่รองรับโดย Vision/CoreImage
    
    Args:
        image: PIL Image
        
    Returns:
        Processed PIL Image
    """
    # แปลงเป็น RGB หรือ RGBA เพื่อให้ใช้งานได้กับ Vision Framework
    if image.mode not in ('RGB', 'RGBA'):
        image = image.convert('RGB')
    
    # ตรวจสอบขนาดภาพและปรับขนาดถ้าใหญ่เกินไป
    max_dimension = 4000  # ขนาดสูงสุดที่แนะนำ (พิกเซล)
    width, height = image.size
    
    if width > max_dimension or height > max_dimension:
        # คำนวณอัตราส่วนการย่อขนาด
        scale_ratio = min(max_dimension / width, max_dimension / height)
        new_width = int(width * scale_ratio)
        new_height = int(height * scale_ratio)
        
        # ปรับขนาดภาพ
        image = image.resize((new_width, new_height), Image.LANCZOS)
    
    return image

def pil_to_ci_image(pil_image: Image.Image) -> Cocoa.CIImage:
    """
    แปลง PIL Image เป็น CIImage
    
    Args:
        pil_image: PIL Image
        
    Returns:
        CIImage object
    """
    # แน่ใจว่าภาพอยู่ในรูปแบบที่เหมาะสม
    if pil_image.mode not in ('RGB', 'RGBA'):
        pil_image = pil_image.convert('RGB')
    
    # แปลงผ่าน PNG data
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    image_data = buffer.getvalue()
    
    # แปลงเป็น NSData
    ns_data = Foundation.NSData.dataWithBytes_length_(image_data, len(image_data))
    
    # สร้าง CIImage จาก NSData
    ci_image = Cocoa.CIImage.imageWithData_(ns_data)
    
    if ci_image is not None:
        return ci_image
    
    # ถ้าวิธี PNG ล้มเหลว, ใช้วิธี TIFF
    buffer = io.BytesIO()
    pil_image.save(buffer, format="TIFF")
    image_data = buffer.getvalue()
    
    # แปลงเป็น NSData
    ns_data = Foundation.NSData.dataWithBytes_length_(image_data, len(image_data))
    
    # สร้าง CIImage จาก NSData
    ci_image = Cocoa.CIImage.imageWithData_(ns_data)
    
    if ci_image is not None:
        return ci_image
    
    # สร้าง NSImage แล้วแปลงเป็น CIImage ถ้าวิธีตรงยังไม่ได้
    ns_image = Cocoa.NSImage.alloc().initWithData_(ns_data)
    ci_image = Cocoa.CIImage.imageWithData_(ns_image.TIFFRepresentation())
    
    if ci_image is not None:
        return ci_image
    
    # ถ้าทั้งหมดล้มเหลว ส่งคืนข้อผิดพลาด
    raise ValueError("Failed to convert PIL Image to CIImage")

def ci_to_pil_image(ci_image: Cocoa.CIImage) -> Image.Image:
    """
    แปลง CIImage กลับเป็น PIL Image
    
    Args:
        ci_image: CIImage object
        
    Returns:
        PIL Image
    """
    try:
        # สร้าง CIContext
        context = Cocoa.CIContext.contextWithOptions_(None)
        
        # ดึงขนาดภาพ
        extent = ci_image.extent()
        width = int(extent.size.width)
        height = int(extent.size.height)
        
        # สร้าง CGImage จาก CIImage
        cg_image = context.createCGImage_fromRect_(ci_image, extent)
        if cg_image is None:
            raise ValueError("Failed to create CGImage from CIImage")
        
        # สร้าง NSBitmapImageRep จาก CGImage
        bitmapRep = Cocoa.NSBitmapImageRep.alloc().initWithCGImage_(cg_image)
        if bitmapRep is None:
            raise ValueError("Failed to create NSBitmapImageRep")
        
        # แปลงเป็นข้อมูล PNG
        png_data = bitmapRep.representationUsingType_properties_(Cocoa.NSPNGFileType, None)
        if png_data is None:
            raise ValueError("Failed to create PNG data")
        
        # แปลงเป็น Python bytes
        python_data = bytes(png_data)
        
        # สร้าง PIL Image จาก bytes
        return Image.open(io.BytesIO(python_data))
    
    except Exception as e:
        # ถ้าวิธีข้างต้นล้มเหลว ลองวิธีที่ 2 
        try:
            print(f"Primary conversion method failed, trying fallback: {str(e)}")
            
            # สร้าง CIContext แบบกำหนดเอง
            options = {
                Cocoa.kCIContextUseSoftwareRenderer: False
            }
            context = Cocoa.CIContext.contextWithOptions_(options)
            
            # ดึงขนาดภาพ
            extent = ci_image.extent()
            
            # สร้าง CGImage
            cg_image = context.createCGImage_fromRect_(ci_image, extent)
            
            # สร้าง NSImage
            ns_image = Cocoa.NSImage.alloc().initWithCGImage_size_(
                cg_image, 
                Cocoa.NSMakeSize(extent.size.width, extent.size.height)
            )
            
            # แปลงเป็น TIFF data
            tiff_data = ns_image.TIFFRepresentation()
            
            # สร้าง PIL Image จาก TIFF data
            return Image.open(io.BytesIO(bytes(tiff_data)))
            
        except Exception as nested_e:
            raise ValueError(f"All conversion methods failed: {str(nested_e)} (original error: {str(e)})")