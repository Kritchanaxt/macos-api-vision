import Vision
import Foundation
import Quartz
import tempfile
import os
import time
from typing import Dict, Any
from PIL import Image

def detect_face_quality(image: Image.Image) -> Dict[str, Any]:
 
    start_time = time.time()
    
    # Save image to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        temp_filename = tmp.name
        image.save(temp_filename, 'PNG')
    
    try:
        # Use NSURL to load the image
        image_url = Foundation.NSURL.fileURLWithPath_(temp_filename)
        
        # Create handler for face detection
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(image_url, None)
        
        # Create requests for face detection
        face_request = Vision.VNDetectFaceRectanglesRequest.alloc().init()
        face_quality_request = Vision.VNDetectFaceCaptureQualityRequest.alloc().init()
        face_landmarks_request = Vision.VNDetectFaceLandmarksRequest.alloc().init()
        
        # Process face detection
        handler.performRequests_error_([face_request], None)
        
        face_results = []
        face_count = 0
        avg_quality = 0.0
        
        # Check results
        if face_request.results():
            face_count = len(face_request.results())
            
            for face_observation in face_request.results():
                # Get face area
                face_bbox = face_observation.boundingBox()
                
                # Analyze face quality
                face_quality_request.setInputFaceObservations_([face_observation])
                handler.performRequests_error_([face_quality_request], None)
                
                quality_score = 0.0
                if face_quality_request.results() and len(face_quality_request.results()) > 0:
                    quality_score = face_quality_request.results()[0].faceCaptureQuality() or 0.0
                
                # Detect landmarks on face
                face_landmarks_request.setInputFaceObservations_([face_observation])
                handler.performRequests_error_([face_landmarks_request], None)
                
                landmarks_detected = False
                if face_landmarks_request.results() and len(face_landmarks_request.results()) > 0:
                    landmarks_detected = True
                
                # Add face data to results
                face_data = {
                    "bbox": {
                        "x": float(face_bbox.origin.x),
                        "y": float(face_bbox.origin.y),
                        "width": float(face_bbox.size.width),
                        "height": float(face_bbox.size.height)
                    },
                    "quality_score": float(quality_score),
                    "has_landmarks": landmarks_detected
                }
                
                face_results.append(face_data)
                avg_quality += quality_score
        
        # Calculate average quality
        if face_count > 0:
            avg_quality = avg_quality / face_count
        
        # Prepare result data
        result = {
            "face_count": face_count,
            "faces": face_results,
            "average_quality": float(avg_quality),
            "processing_time": time.time() - start_time
        }
        
        return result
    
    except Exception as e:
        return {
            "error": f"Error occurred: {str(e)}",
            "face_count": 0,
            "faces": [],
            "average_quality": 0.0,
            "processing_time": time.time() - start_time
        }
    finally:
        # Delete temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)