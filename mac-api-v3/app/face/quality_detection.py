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
    
    # Get image dimensions
    dimensions = get_image_dimensions(image)
    width, height = dimensions["width"], dimensions["height"]
    
    # Create a copy of the image for drawing
    output_image = image.copy()
    draw = ImageDraw.Draw(output_image)
    
    # Save image to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        temp_filename = tmp.name
        image.save(temp_filename, 'PNG')
    
    try:
        image_url = Foundation.NSURL.fileURLWithPath_(temp_filename)
        
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(image_url, None)
        
        # Create requests for face detection
        face_request = Vision.VNDetectFaceRectanglesRequest.alloc().init()
        face_quality_request = Vision.VNDetectFaceCaptureQualityRequest.alloc().init()
        face_landmarks_request = Vision.VNDetectFaceLandmarksRequest.alloc().init()
        
        # Process face detection
        handler.performRequests_error_([face_request], None)
        
        face_results = []
        face_count = 0
        
        # Check results
        if face_request.results():
            face_count = len(face_request.results())
            
            for i, face_observation in enumerate(face_request.results()):
                # Get face area
                face_bbox = face_observation.boundingBox()
                
                # Convert normalized coordinates to pixel coordinates
                x = int(face_bbox.origin.x * width)
                y = int(face_bbox.origin.y * height)
                w = int(face_bbox.size.width * width)
                h = int(face_bbox.size.height * height)
            
                rect_y = height - y - h
                
                box_color = (255, 0, 0)  # Default red
                
                # Analyze face quality
                face_quality_request.setInputFaceObservations_([face_observation])
                handler.performRequests_error_([face_quality_request], None)
                
                quality_score = 0.0
                if face_quality_request.results() and len(face_quality_request.results()) > 0:
                    quality_score = face_quality_request.results()[0].faceCaptureQuality() or 0.0
                    
                    # Adjust color based on quality score
                    if quality_score > 0.7:
                        box_color = (0, 255, 0)  # Good quality - green
                    elif quality_score > 0.4:
                        box_color = (255, 255, 0)  # Medium quality - yellow
                
                # Draw rectangle with 3-pixel width
                draw.rectangle([x, rect_y, x + w, rect_y + h], outline=box_color, width=3)
                
                # Add quality score text
                font_size = max(10, int(h/10))
                draw.text((x, rect_y - font_size - 5), f"Q: {quality_score:.2f}", fill=box_color)
                
                # Detect landmarks on face
                face_landmarks_request.setInputFaceObservations_([face_observation])
                handler.performRequests_error_([face_landmarks_request], None)
                
                landmarks_detected = False
                if face_landmarks_request.results() and len(face_landmarks_request.results()) > 0:
                    landmarks_detected = True
                
                # Add face data to results with id field (converted to string)
                face_data = {
                    "id": str(i + 1),  # Add id field as a string
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
        
        # Calculate rates
        fast_rate = calculate_fast_rate(width, height)
        rack_cooling_rate = calculate_rack_cooling_rate(width, height, face_count)
        
        # Prepare result data
        result = {
            "faces": face_results,
            "dimensions": dimensions,
            "fast_rate": fast_rate,
            "rack_cooling_rate": rack_cooling_rate,
            "processing_time": time.time() - start_time,
            "output_image": output_image  # Return the image with bounding boxes
        }
        
        return result
    
    except Exception as e:
        return {
            "error": f"Error occurred: {str(e)}",
            "faces": [],
            "dimensions": dimensions,
            "fast_rate": calculate_fast_rate(width, height),
            "rack_cooling_rate": calculate_rack_cooling_rate(width, height, 0),
            "processing_time": time.time() - start_time,
            "output_image": image  # Return original image in case of error
        }
    finally:
        # Delete temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)