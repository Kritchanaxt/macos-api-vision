import Vision
import Quartz
import Foundation
import time
import os
import tempfile
from typing import List, Dict, Any
from PIL import Image, ImageDraw
from app.utils.image_utils import get_image_dimensions, calculate_fast_rate, calculate_rack_cooling_rate


def process_image_with_vision(image, languages: List[str], recognition_level: str = "accurate") -> Dict[str, Any]:
   
    start_time = time.time()
    
    # Get image dimensions
    dimensions = get_image_dimensions(image)
    width, height = dimensions["width"], dimensions["height"]
    
    # Add unit to dimensions
    dimensions["unit"] = "pixel"
    
    # Save image to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        temp_filename = tmp.name
        image.save(temp_filename, 'PNG')
    
    try:
        # Use NSURL to load the image
        image_url = Foundation.NSURL.fileURLWithPath_(temp_filename)
        
        # Create handler for text recognition
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(image_url, None)
        
        # Configure options for text recognition
        recognition_level_value = Vision.VNRequestTextRecognitionLevelAccurate if recognition_level == "accurate" else Vision.VNRequestTextRecognitionLevelFast
        
        # Create request for text recognition
        text_request = Vision.VNRecognizeTextRequest.alloc().init()
        text_request.setRecognitionLevel_(recognition_level_value)
        text_request.setUsesLanguageCorrection_(True)
        
        # Add Thai language support
        ns_languages = Foundation.NSArray.arrayWithObjects_(*languages)
        text_request.setRecognitionLanguages_(ns_languages)
        
        # Process OCR
        error_ptr = Foundation.NSError.alloc().init()
        success = handler.performRequests_error_([text_request], None)
        
        # Get recognized text
        results = text_request.results()
        
        recognized_text = ""
        confidence_sum = 0
        text_object_count = 0
        text_elements = []
        
        # Create a copy of the image to draw bounding boxes for visualization
        visualization_image = image.copy()
        draw = ImageDraw.Draw(visualization_image)
        
        if results:
            text_object_count = len(results)
            for idx, result in enumerate(results):
                # Extract text and confidence
                text = result.text()
                confidence = result.confidence()
                
                # Add recognized text
                recognized_text += text + "\n"
                
                # Calculate average confidence
                confidence_sum += confidence
                
                # Get bounding box
                # In Vision framework, boundingBox() returns a CGRect in normalized coordinates (0-1)
                bbox = result.boundingBox()
                
                # Convert normalized coordinates to actual pixel values
                x = bbox.origin.x * width
                y = (1 - bbox.origin.y - bbox.size.height) * height  # Flip Y coordinate
                w = bbox.size.width * width
                h = bbox.size.height * height
                
                # Create unique ID for text element
                element_id = f"element_{idx+1}"
                
                # Add to text elements array with ID and unit
                text_elements.append({
                    "id": element_id,
                    "text": text,
                    "confidence": float(confidence),
                    "position": {
                        "x": float(x),
                        "y": float(y),
                        "width": float(w),
                        "height": float(h),
                        "unit": "pixel"
                    }
                })
                
                # Draw bounding box on visualization image
                draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
                # Add text label (first 10 chars or less)
                label = text[:10] + "..." if len(text) > 10 else text
                draw.text((x, y - 10), label, fill="red")
        
        # Calculate average confidence
        avg_confidence = confidence_sum / len(results) if results else 0
        
        # Calculate rates
        fast_rate = calculate_fast_rate(width, height)
        rack_cooling_rate = calculate_rack_cooling_rate(width, height, text_object_count)
        
        # Save visualization image for debugging
        visualization_path = temp_filename + "_vis.png"
        visualization_image.save(visualization_path)
        
        return {
            "text": recognized_text.strip(),
            "confidence": float(avg_confidence),
            "text_elements": text_elements,
            "dimensions": dimensions,
            "fast_rate": fast_rate,
            "rack_cooling_rate": rack_cooling_rate,
            "processing_time": time.time() - start_time,
            "text_object_count": text_object_count,
            "visualization_image": visualization_image
        }
    
    except Exception as e:
        return {
            "text": f"Error occurred: {str(e)}",
            "confidence": 0.0,
            "text_elements": [],
            "dimensions": dimensions,
            "fast_rate": calculate_fast_rate(width, height),
            "rack_cooling_rate": calculate_rack_cooling_rate(width, height, 0),
            "processing_time": time.time() - start_time,
            "text_object_count": 0
        }
    finally:
        # Delete temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)