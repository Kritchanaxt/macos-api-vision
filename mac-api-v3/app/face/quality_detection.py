import Vision
import Foundation
import Quartz
import tempfile
import os
import time
from typing import Dict, Any
from PIL import Image, ImageDraw
from app.utils.image_utils import get_image_dimensions, calculate_fast_rate, calculate_rack_cooling_rate

def detect_face_quality(image: Image.Image) -> Dict[str, Any]:
    start_time = time.time()
    
    dimensions = get_image_dimensions(image)
    width, height = dimensions["width"], dimensions["height"]
    
    output_image = image.copy()
    draw = ImageDraw.Draw(output_image)
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        temp_filename = tmp.name
        image.save(temp_filename, 'PNG')
    
    try:
        image_url = Foundation.NSURL.fileURLWithPath_(temp_filename)
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(image_url, None)
        
        face_request = Vision.VNDetectFaceRectanglesRequest.alloc().init()
        face_quality_request = Vision.VNDetectFaceCaptureQualityRequest.alloc().init()
        face_landmarks_request = Vision.VNDetectFaceLandmarksRequest.alloc().init()
        
        handler.performRequests_error_([face_request], None)
        
        face_results = []
        face_count = 0
        has_face = False
        quality_score = None
        position = None
        
        if face_request.results():
            face_count = len(face_request.results())
            has_face = face_count > 0
            
            for i, face_observation in enumerate(face_request.results()):
                face_bbox = face_observation.boundingBox()
                
                x = int(face_bbox.origin.x * width)
                y = int(face_bbox.origin.y * height)
                w = int(face_bbox.size.width * width)
                h = int(face_bbox.size.height * height)
                rect_y = height - y - h
                
                # Default color = Green
                box_color = (0, 255, 0)
                
                # Analyze face quality
                face_quality_request.setInputFaceObservations_([face_observation])
                handler.performRequests_error_([face_quality_request], None)
                
                current_quality_score = 0.0
                if face_quality_request.results() and len(face_quality_request.results()) > 0:
                    current_quality_score = face_quality_request.results()[0].faceCaptureQuality() or 0.0
                    
                    # Keep the best quality score and position
                    if quality_score is None or current_quality_score > quality_score:
                        quality_score = current_quality_score
                        position = {
                            "x": float(face_bbox.origin.x),
                            "y": float(face_bbox.origin.y),
                            "width": float(face_bbox.size.width),
                            "height": float(face_bbox.size.height)
                        }
                                    
                # Draw rectangle and quality score
                draw.rectangle([x, rect_y, x + w, rect_y + h], outline=box_color, width=3)
                font_size = max(10, int(h / 10))
                draw.text((x, rect_y - font_size - 5), f"Q: {current_quality_score:.2f}", fill=box_color)
                
                # Landmarks detection
                face_landmarks_request.setInputFaceObservations_([face_observation])
                handler.performRequests_error_([face_landmarks_request], None)
                landmarks_detected = False
                if face_landmarks_request.results() and len(face_landmarks_request.results()) > 0:
                    landmarks_detected = True
                
                face_data = {
                    "id": str(i + 1),
                    "bbox": {
                        "x": float(face_bbox.origin.x),
                        "y": float(face_bbox.origin.y),
                        "width": float(face_bbox.size.width),
                        "height": float(face_bbox.size.height)
                    },
                    "quality_score": float(current_quality_score),
                    "has_landmarks": landmarks_detected
                }
                
                face_results.append(face_data)
        
        fast_rate = calculate_fast_rate(width, height)
        rack_cooling_rate = calculate_rack_cooling_rate(width, height, face_count)
        
        result = {
            "has_face": has_face,
            "face_count": face_count,
            "quality_score": quality_score,
            "position": position,
            "faces": face_results,
            "dimensions": dimensions,
            "fast_rate": fast_rate,
            "rack_cooling_rate": rack_cooling_rate,
            "processing_time": time.time() - start_time,
            "output_image": output_image
        }
        return result
    
    except Exception as e:
        return {
            "has_face": False,
            "face_count": 0,
            "quality_score": None,
            "position": None,
            "error": f"Error occurred: {str(e)}",
            "faces": [],
            "dimensions": dimensions,
            "fast_rate": calculate_fast_rate(width, height),
            "rack_cooling_rate": calculate_rack_cooling_rate(width, height, 0),
            "processing_time": time.time() - start_time,
            "output_image": image
        }
    finally:
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)
