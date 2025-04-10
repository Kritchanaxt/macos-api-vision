import Vision
import Foundation
import Quartz
import numpy as np
import tempfile
import os
import time
from typing import Dict, Any, List, Tuple
from PIL import Image
from app.utils.image_utils import get_image_dimensions, calculate_fast_rate, calculate_rack_cooling_rate

def detect_card(image: Image.Image) -> Dict[str, Any]:
    
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
        
        # Create handler for pattern detection
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(image_url, None)
        
        # Create request for rectangle detection
        rectangle_request = Vision.VNDetectRectanglesRequest.alloc().init()
        rectangle_request.setMinimumAspectRatio_(0.5)  
        rectangle_request.setMaximumAspectRatio_(2.0)  
        rectangle_request.setMinimumSize_(0.2)  
        rectangle_request.setMaximumObservations_(5)  
        
        # Process rectangle detection
        handler.performRequests_error_([rectangle_request], None)
        
        # Prepare results
        cards = []
        
        # Check results
        if rectangle_request.results():
            for i, rectangle_observation in enumerate(rectangle_request.results()):
                # Get rectangle coordinates
                rectangle_box = rectangle_observation.boundingBox()
                confidence = rectangle_observation.confidence()
                
                # Convert to 4 corner coordinates
                corners = _convert_bounding_box_to_corners(rectangle_box)
                
                # Add card data to results
                card_data = {
                    "id": i + 1,
                    "corners": corners,
                    "confidence": float(confidence),
                    "bbox": {
                        "x": float(rectangle_box.origin.x),
                        "y": float(rectangle_box.origin.y),
                        "width": float(rectangle_box.size.width),
                        "height": float(rectangle_box.size.height)
                    }
                }
                
                cards.append(card_data)
        
        # Calculate rates
        card_count = len(cards)
        fast_rate = calculate_fast_rate(width, height)
        rack_cooling_rate = calculate_rack_cooling_rate(width, height, card_count)
        
        return {
            "card_count": card_count,
            "cards": cards,
            "dimensions": dimensions,
            "fast_rate": fast_rate,
            "rack_cooling_rate": rack_cooling_rate,
            "processing_time": time.time() - start_time
        }
    
    except Exception as e:
        return {
            "error": f"Error occurred: {str(e)}",
            "card_count": 0,
            "cards": [],
            "dimensions": dimensions,
            "fast_rate": calculate_fast_rate(width, height),
            "rack_cooling_rate": calculate_rack_cooling_rate(width, height, 0),
            "processing_time": time.time() - start_time
        }
    finally:
        # Delete temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)

def _convert_bounding_box_to_corners(bbox) -> List[Dict[str, float]]:

    # Extract bounding box values
    x = float(bbox.origin.x)
    y = float(bbox.origin.y)
    width = float(bbox.size.width)
    height = float(bbox.size.height)
    
    # Calculate coordinates for all 4 corners
    # Vision framework uses coordinate system with (0,0) at bottom-left
    corners = [
        {"x": x, "y": y},  # Bottom-left corner
        {"x": x + width, "y": y},  # Bottom-right corner
        {"x": x + width, "y": y + height},  # Top-right corner
        {"x": x, "y": y + height}  # Top-left corner
    ]
    
    return corners