from typing import List, Dict, Any
from PIL import Image
import re

# Import the processing function
try:
    from app.ocr.vision_ocr import process_image_with_vision
    from app.ocr.document_classifier import classify_document_type
except ImportError:
    try:
        from ocr.vision_ocr import process_image_with_vision
        from ocr.document_classifier import classify_document_type
    except ImportError:
        # For direct testing
        from vision_ocr import process_image_with_vision
        from document_classifier import classify_document_type


def organize_text_elements_into_lines(text_elements: List[Dict]) -> Dict[str, Dict]:
    """
    Organize text elements into lines based on their vertical position
    Returns a dictionary with keys like 'line_1', 'line_2', etc. with clear IDs
    """
    if not text_elements:
        return {}
    
    # Sort elements by Y position (top to bottom)
    sorted_elements = sorted(text_elements, key=lambda x: x["position"]["y"])
    
    # Group elements by approximate Y position (consider elements on the same line if within 20px)
    lines = []
    current_line = [sorted_elements[0]]
    current_y = sorted_elements[0]["position"]["y"]
    
    for element in sorted_elements[1:]:
        if abs(element["position"]["y"] - current_y) < 20:
            # Same line
            current_line.append(element)
        else:
            # New line
            lines.append(current_line)
            current_line = [element]
            current_y = element["position"]["y"]
    
    # Add the last line
    if current_line:
        lines.append(current_line)
    
    # For each line, sort elements by X position (left to right)
    # and create a single TextLine object
    text_lines = {}
    for i, line in enumerate(lines):
        # Sort by X position
        line_elements = sorted(line, key=lambda x: x["position"]["x"])
        
        # Create line ID
        line_id = f"line_{i+1}"
        
        # Combine text
        line_text = " ".join([elem["text"] for elem in line_elements])
        
        # Calculate average confidence
        avg_confidence = sum([elem["confidence"] for elem in line_elements]) / len(line_elements)
        
        # Calculate combined position
        min_x = min([elem["position"]["x"] for elem in line_elements])
        min_y = min([elem["position"]["y"] for elem in line_elements])
        max_x = max([elem["position"]["x"] + elem["position"]["width"] for elem in line_elements])
        max_y = max([elem["position"]["y"] + elem["position"]["height"] for elem in line_elements])
        
        text_lines[line_id] = {
            "id": line_id,
            "text": line_text,
            "confidence": avg_confidence,
            "position": {
                "x": min_x,
                "y": min_y,
                "width": max_x - min_x,
                "height": max_y - min_y,
                "unit": "pixel"
            }
        }
    
    return text_lines


def perform_ocr(image: Image.Image, languages: List[str], recognition_level: str) -> Dict[str, Any]:
    """
    Perform OCR on the image and return structured data with improved formatting
    for frontend consumption
    """
    # Check if Thai language is in the list
    if "th-TH" not in languages and "th" not in languages:
        # Add Thai support automatically
        languages = ["th-TH"] + languages
    
    # Call OCR function from Vision Framework
    ocr_result = process_image_with_vision(image, languages, recognition_level)
    
    # Get the full recognized text
    recognized_text = ocr_result.get("text", "")
    
    # Try to classify document type
    document_type = classify_document_type(recognized_text, ocr_result.get("text_elements", []))
    
    # Organize text elements into lines with clear IDs
    text_lines = organize_text_elements_into_lines(ocr_result.get("text_elements", []))
    
    # Add unit to dimensions
    dimensions = ocr_result.get("dimensions", {"width": 0, "height": 0})
    dimensions["unit"] = "pixel"
    
    # Return the complete structured result
    return {
        "document_type": document_type,
        "recognized_text": recognized_text,
        "confidence": ocr_result.get("confidence", 0.0),
        "text_lines": text_lines,
        "dimensions": dimensions,
        "fast_rate": ocr_result.get("fast_rate", 0.0),
        "rack_cooling_rate": ocr_result.get("rack_cooling_rate", 0.0),
        "processing_time": ocr_result.get("processing_time", 0.0),
        "text_object_count": ocr_result.get("text_object_count", 0),
        "visualization_image": ocr_result.get("visualization_image", None),
        "output_path": ocr_result.get("output_path", None)
    }