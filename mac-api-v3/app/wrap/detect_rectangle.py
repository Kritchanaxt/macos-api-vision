from Vision import VNImageRequestHandler, VNDetectRectanglesRequest
from Cocoa import CIImage
from Foundation import NSPoint

def detect_document_edges(image: CIImage):
    """
    ตรวจจับขอบเอกสารในภาพด้วย Vision Framework
    Args:
        image: CIImage object จาก CoreImage
    Returns:
        tuple: จุดมุม 4 จุดของสี่เหลี่ยม (top_left, top_right, bottom_right, bottom_left)
    """
    request = VNDetectRectanglesRequest.alloc().init()
    request.minimumAspectRatio = 0.2
    request.maximumAspectRatio = 1.0
    request.minimumSize = 0.1
    request.maximumObservations = 1

    handler = VNImageRequestHandler.alloc().initWithCIImage_options_(image, None)
    handler.performRequests_error_([request], None)
    
    if request.results() and len(request.results()) > 0:
        observation = request.results()[0]
        top_left = NSPoint(observation.topLeft().x * image.extent().size.width,
                          observation.topLeft().y * image.extent().size.height)
        top_right = NSPoint(observation.topRight().x * image.extent().size.width,
                           observation.topRight().y * image.extent().size.height)
        bottom_right = NSPoint(observation.bottomRight().x * image.extent().size.width,
                              observation.bottomRight().y * image.extent().size.height)
        bottom_left = NSPoint(observation.bottomLeft().x * image.extent().size.width,
                             observation.bottomLeft().y * image.extent().size.height)
        return top_left, top_right, bottom_right, bottom_left
    else:
        raise ValueError("ไม่พบขอบเอกสารในภาพ")