from Vision import VNImageRequestHandler, VNDetectRectanglesRequest
from Cocoa import CIImage
from Quartz import CIVector
import objc

def detect_document_edges(image: CIImage):
    """
    ตรวจจับขอบเอกสารในภาพด้วย Vision Framework
    Args:
        image: CIImage object จาก CoreImage
    Returns:
        tuple: จุดมุม 4 จุดของสี่เหลี่ยม (top_left, top_right, bottom_right, bottom_left) as CIVectors
    """
    try:
        # Create rectangle detection request
        request = VNDetectRectanglesRequest.alloc().init()
        request.setMinimumAspectRatio_(0.2)
        request.setMaximumAspectRatio_(1.0)
        request.setMinimumSize_(0.1)
        request.setMaximumObservations_(1)
        request.setQuadratureTolerance_(10.0)  # Allow some deviation from perfect rectangles

        # Create image request handler with CIImage
        error_ptr = objc.pyobjc_id(None)  # Error pointer for Objective-C
        handler = VNImageRequestHandler.alloc().initWithCIImage_options_(image, None)
        success = handler.performRequests_error_([request], error_ptr)
        
        if not success:
            error = error_ptr.value()
            if error:
                raise ValueError(f"Vision Request Error: {error.localizedDescription()}")
            else:
                raise ValueError("Unknown error in Vision request")
        
        # Check if we have results
        results = request.results()
        if results and len(results) > 0:
            observation = results[0]
            img_width = image.extent().size.width
            img_height = image.extent().size.height
            
            # Get normalized coordinates
            # Use consistent access methods by first trying property access then method calls
            try:
                # Try property access (lower case)
                tl_x, tl_y = observation.topLeft().x, observation.topLeft().y
                tr_x, tr_y = observation.topRight().x, observation.topRight().y
                br_x, br_y = observation.bottomRight().x, observation.bottomRight().y
                bl_x, bl_y = observation.bottomLeft().x, observation.bottomLeft().y
            except AttributeError:
                # Try method calls (upper case)
                tl_x, tl_y = observation.topLeft().X(), observation.topLeft().Y()
                tr_x, tr_y = observation.topRight().X(), observation.topRight().Y()
                br_x, br_y = observation.bottomRight().X(), observation.bottomRight().Y()
                bl_x, bl_y = observation.bottomLeft().X(), observation.bottomLeft().Y()
            
            # Convert normalized coordinates to image coordinates
            # Return as CIVectors to ensure compatibility with CoreImage filters
            top_left = CIVector.vectorWithX_Y_(tl_x * img_width, tl_y * img_height)
            top_right = CIVector.vectorWithX_Y_(tr_x * img_width, tr_y * img_height)
            bottom_right = CIVector.vectorWithX_Y_(br_x * img_width, br_y * img_height)
            bottom_left = CIVector.vectorWithX_Y_(bl_x * img_width, bl_y * img_height)
            
            return top_left, top_right, bottom_right, bottom_left
        else:
            raise ValueError("ไม่พบขอบเอกสารในภาพ")
    except Exception as e:
        print(f"Error detecting document edges: {str(e)}")
        raise ValueError(f"ไม่สามารถตรวจจับขอบเอกสาร: {str(e)}")