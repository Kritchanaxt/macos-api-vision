from Vision import VNImageRequestHandler, VNDetectRectanglesRequest
from Cocoa import CIImage
from Quartz import CIVector
import objc
from Foundation import NSError

def detect_document_edges(image: CIImage):
    """
    ตรวจจับขอบเอกสารในภาพด้วย Vision Framework
    Args:
        image: CIImage object จาก CoreImage
    Returns:
        tuple: จุดมุม 4 จุดของสี่เหลี่ยม (top_left, top_right, bottom_right, bottom_left) as CIVectors
    """
    try:
        # สร้าง request สำหรับตรวจจับสี่เหลี่ยม
        request = VNDetectRectanglesRequest.alloc().init()
        
        # ปรับค่าพารามิเตอร์เพื่อเพิ่มความแม่นยำ
        request.setMinimumAspectRatio_(0.2)  # อัตราส่วนขั้นต่ำที่น้อยลงเพื่อรองรับเอกสารหลายขนาด
        request.setMaximumAspectRatio_(1.0)  # อัตราส่วนสูงสุด (1.0 หมายถึงสี่เหลี่ยมจัตุรัส)
        request.setMinimumSize_(0.15)  # ลดขนาดขั้นต่ำลงเพื่อให้จับเอกสารได้ง่ายขึ้น
        request.setMaximumObservations_(3)  # เพิ่มจำนวนสี่เหลี่ยมที่ตรวจจับได้เป็น 3 แล้วเลือกตัวที่เหมาะสมที่สุด
        request.setQuadratureTolerance_(20.0)  # เพิ่มค่าความทนทานเพื่อให้รองรับเอกสารที่ถูกถ่ายเอียงมากขึ้น
        request.setMinimumConfidence_(0.5)  # ลดค่าความเชื่อมั่นขั้นต่ำลงเพื่อเพิ่มโอกาสการตรวจจับ
        
        # สร้าง image request handler ด้วย CIImage
        error_ptr = NSError.alloc().init()
        handler = VNImageRequestHandler.alloc().initWithCIImage_options_(image, None)
        success = handler.performRequests_error_([request], error_ptr)
        
        if not success:
            if error_ptr:
                raise ValueError(f"Vision Request Error: {error_ptr.localizedDescription()}")
            else:
                raise ValueError("Unknown error in Vision request")
        
        # ตรวจสอบผลลัพธ์
        results = request.results()
        if results and len(results) > 0:
            # เลือกผลลัพธ์ที่มีความเชื่อมั่นสูงสุด
            best_observation = None
            highest_confidence = 0.0
            
            for observation in results:
                confidence = observation.confidence()
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_observation = observation
            
            if best_observation is None:
                raise ValueError("ไม่พบขอบเอกสารที่มีความเชื่อมั่นเพียงพอ")
                
            img_width = image.extent().size.width
            img_height = image.extent().size.height
            
            # แก้ไขการอ่านค่าพิกัดโดยตรงและปลอดภัยมากขึ้น
            # ดึงข้อมูลจากพิกัดมุม
            try:
                # แยกชัดเจนระหว่าง topLeft, topRight ฯลฯ ซึ่งเป็น properties และการเรียกใช้ค่า x, y
                top_left_point = best_observation.topLeft()
                top_right_point = best_observation.topRight()
                bottom_right_point = best_observation.bottomRight()
                bottom_left_point = best_observation.bottomLeft()
                
                # แปลงพิกัดที่ normalized เป็นพิกัดของภาพจริง
                # ใช้รูปแบบที่ชัดเจนในการสร้าง CIVector
                top_left = CIVector.vectorWithX_Y_(
                    top_left_point.x * img_width, 
                    (1 - top_left_point.y) * img_height
                )
                top_right = CIVector.vectorWithX_Y_(
                    top_right_point.x * img_width, 
                    (1 - top_right_point.y) * img_height
                )
                bottom_right = CIVector.vectorWithX_Y_(
                    bottom_right_point.x * img_width, 
                    (1 - bottom_right_point.y) * img_height
                )
                bottom_left = CIVector.vectorWithX_Y_(
                    bottom_left_point.x * img_width, 
                    (1 - bottom_left_point.y) * img_height
                )
                
                return top_left, top_right, bottom_right, bottom_left
            
            except Exception as e:
                print(f"Error extracting rectangle points: {str(e)}")
                raise ValueError(f"ไม่สามารถอ่านค่าพิกัดสี่เหลี่ยม: {str(e)}")
        else:
            raise ValueError("ไม่พบขอบเอกสารในภาพ")
    
    except Exception as e:
        print(f"Error detecting document edges: {str(e)}")
        # สร้างขอบเริ่มต้นโดยใช้ขอบของภาพ (ขยับเข้ามา 5%)
        img_width = image.extent().size.width
        img_height = image.extent().size.height
        margin = 0.05  # 5% margin
        
        top_left = CIVector.vectorWithX_Y_(img_width * margin, img_height * margin)
        top_right = CIVector.vectorWithX_Y_(img_width * (1 - margin), img_height * margin)
        bottom_right = CIVector.vectorWithX_Y_(img_width * (1 - margin), img_height * (1 - margin))
        bottom_left = CIVector.vectorWithX_Y_(img_width * margin, img_height * (1 - margin))
        
        return top_left, top_right, bottom_right, bottom_left