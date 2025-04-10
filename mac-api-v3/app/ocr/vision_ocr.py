import Vision
import Quartz
import Foundation
import time
import os
import tempfile
from typing import List, Dict, Any
from PIL import Image
from app.utils.image_utils import get_image_dimensions, calculate_fast_rate, calculate_rack_cooling_rate


def process_image_with_vision(image, languages: List[str], recognition_level: str = "accurate") -> Dict[str, Any]:
   
    start_time = time.time()
    
    # Get image dimensions
    dimensions = get_image_dimensions(image)
    width, height = dimensions["width"], dimensions["height"]
    
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
        detected_languages = set()
        text_object_count = 0
        
        if results:
            text_object_count = len(results)
            for result in results:
                # Add recognized text
                recognized_text += result.text() + "\n"
                
                # Calculate average confidence
                confidence_sum += result.confidence()
                
                # Detect recognized languages
                if hasattr(result, "recognizedLanguages"):
                    for lang in result.recognizedLanguages():
                        detected_languages.add(lang.string())
        
        # Calculate average confidence
        avg_confidence = confidence_sum / len(results) if results else 0
        
        # Calculate rates
        fast_rate = calculate_fast_rate(width, height)
        rack_cooling_rate = calculate_rack_cooling_rate(width, height, text_object_count)
        
        return {
            "text": recognized_text.strip(),
            "confidence": float(avg_confidence),
            "languages_detected": list(detected_languages),
            "dimensions": dimensions,
            "fast_rate": fast_rate,
            "rack_cooling_rate": rack_cooling_rate,
            "text_object_count": text_object_count,
            "processing_time": time.time() - start_time
        }
    
    except Exception as e:
        return {
            "text": f"Error occurred: {str(e)}",
            "confidence": 0.0,
            "languages_detected": [],
            "dimensions": dimensions,
            "fast_rate": calculate_fast_rate(width, height),
            "rack_cooling_rate": calculate_rack_cooling_rate(width, height, 0),
            "text_object_count": 0,
            "processing_time": time.time() - start_time
        }
    finally:
        # Delete temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)