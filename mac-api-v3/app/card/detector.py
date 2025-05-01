import Vision
import Foundation
import Quartz
import numpy as np
import tempfile
import os
import time
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw
from app.utils.image_utils import get_image_dimensions, calculate_fast_rate, calculate_rack_cooling_rate

def detect_card(image: Image.Image) -> Dict[str, Any]:
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

                rectangle_box = rectangle_observation.boundingBox()
                confidence = rectangle_observation.confidence()
                
                # Convert normalized coordinates (0-1) to pixel coordinates
                x = int(rectangle_box.origin.x * width)
                y = int(rectangle_box.origin.y * height)
                w = int(rectangle_box.size.width * width)
                h = int(rectangle_box.size.height * height)
                
                rect_y = height - y - h
                
                # Select color based on confidence
                if confidence > 0.8:
                    box_color = (0, 255, 0)  # High confidence - green
                elif confidence > 0.5:
                    box_color = (255, 255, 0)  # Medium confidence - yellow
                else:
                    box_color = (255, 0, 0)  # Low confidence - red
                
                # Draw rectangle with 3-pixel width
                draw.rectangle([x, rect_y, x + w, rect_y + h], outline=box_color, width=3)
                
                # Add card ID and confidence
                draw.text((x, rect_y - 20), f"Card #{i+1} ({confidence:.2f})", fill=box_color)
                
                # Convert to 4 corner coordinates
                corners = _convert_bounding_box_to_corners(rectangle_box)
                
                # Draw corners as small circles
                corner_radius = 5
                for corner in corners:
                    corner_x = int(corner["x"] * width)
                    corner_y = height - int(corner["y"] * height)  # Convert to PIL coordinates
                    draw.ellipse((corner_x - corner_radius, corner_y - corner_radius, 
                                  corner_x + corner_radius, corner_y + corner_radius), 
                                  fill=box_color)
                
                # Add card data to results
                card_data = {
                    "id": str(i + 1),
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
            "cards": cards,
            "dimensions": dimensions,
            "fast_rate": fast_rate,
            "rack_cooling_rate": rack_cooling_rate,
            "processing_time": time.time() - start_time,
            "output_image": output_image  # Return the image with bounding boxes
        }
    
    except Exception as e:
        return {
            "error": f"Error occurred: {str(e)}",
            "cards": [],
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