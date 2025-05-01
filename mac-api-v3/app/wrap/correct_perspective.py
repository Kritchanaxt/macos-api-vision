from Cocoa import CIImage, CIFilter
from Foundation import NSNumber
from Quartz import CIVector
import objc

def correct_perspective(image: CIImage, top_left, top_right, bottom_right, bottom_left):
    """
    ปรับเปอร์สเปคทีฟและครอบตัดภาพด้วย CoreImage
    Args:
        image: CIImage object จาก CoreImage
        top_left, top_right, bottom_right, bottom_left: จุดมุมของสี่เหลี่ยม (CIVector หรืออื่นๆ)
    Returns:
        CIImage: ภาพที่ปรับเปอร์สเปคทีฟแล้ว
    """
    try:
        # สร้าง perspective correction filter
        filter = CIFilter.filterWithName_("CIPerspectiveCorrection")
        if filter is None:
            raise ValueError("ไม่สามารถสร้าง CIPerspectiveCorrection filter ได้")
        
        # แปลงจุดเป็น CIVector อย่างปลอดภัย
        def ensure_ci_vector(point):
            # ถ้าเป็น CIVector อยู่แล้ว ส่งคืนเลย
            if isinstance(point, CIVector):
                return point
                
            # ถ้าเป็นชนิดอื่น พยายามอ่านค่า x, y
            try:
                # วิธีที่ 1: Point มี property x, y (lowercase)
                if hasattr(point, 'x') and hasattr(point, 'y'):
                    x = float(point.x)
                    y = float(point.y)
                    return CIVector.vectorWithX_Y_(x, y)
                
                # วิธีที่ 2: Point มี method X(), Y() (uppercase)
                elif hasattr(point, 'X') and hasattr(point, 'Y'):
                    x = float(point.X())
                    y = float(point.Y())
                    return CIVector.vectorWithX_Y_(x, y)
                
                # วิธีที่ 3: Point เป็น dict with 'x', 'y' keys
                elif isinstance(point, dict) and 'x' in point and 'y' in point:
                    x = float(point['x'])
                    y = float(point['y'])
                    return CIVector.vectorWithX_Y_(x, y)
                    
                # วิธีที่ 4: Point เป็น tuple หรือ list
                elif hasattr(point, '__len__') and len(point) >= 2:
                    x = float(point[0])
                    y = float(point[1])
                    return CIVector.vectorWithX_Y_(x, y)
                    
                else:
                    raise TypeError(f"ไม่รู้จักชนิดของจุด: {type(point)}")
            
            except Exception as e:
                raise ValueError(f"ไม่สามารถแปลงจุดเป็น CIVector: {type(point)} - {str(e)}")
        
        # แปลงทุกจุดให้เป็น CIVector
        ci_top_left = ensure_ci_vector(top_left)
        ci_top_right = ensure_ci_vector(top_right)
        ci_bottom_right = ensure_ci_vector(bottom_right)
        ci_bottom_left = ensure_ci_vector(bottom_left)
        
        # ตั้งค่า input parameters
        filter.setValue_forKey_(image, "inputImage")
        filter.setValue_forKey_(ci_top_left, "inputTopLeft")
        filter.setValue_forKey_(ci_top_right, "inputTopRight")
        filter.setValue_forKey_(ci_bottom_right, "inputBottomRight")
        filter.setValue_forKey_(ci_bottom_left, "inputBottomLeft")
        
        # รับ output image
        output_image = filter.valueForKey_("outputImage")
        if output_image is None:
            raise ValueError("ไม่สามารถปรับเปอร์สเปคทีฟได้")
        
        return output_image
    
    except Exception as e:
        print(f"Error in perspective correction: {str(e)}")
        raise ValueError(f"ไม่สามารถปรับเปอร์สเปคทีฟ: {str(e)}")