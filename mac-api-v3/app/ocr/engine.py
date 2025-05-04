from typing import List, Dict, Any
from PIL import Image
import re

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

    if not text_elements:
        return {}
    
    sorted_elements = sorted(text_elements, key=lambda x: x["position"]["y"])
    
    lines = []
    current_line = [sorted_elements[0]]
    current_y = sorted_elements[0]["position"]["y"]
    
    for element in sorted_elements[1:]:
        if abs(element["position"]["y"] - current_y) < 20:
            current_line.append(element)
        else:
            lines.append(current_line)
            current_line = [element]
            current_y = element["position"]["y"]
    
    if current_line:
        lines.append(current_line)
    
    text_lines = {}
    for i, line in enumerate(lines):
        line_elements = sorted(line, key=lambda x: x["position"]["x"])
        
        line_id = f"line_{i+1}"
        
        line_text = " ".join([elem["text"] for elem in line_elements])
        
        avg_confidence = sum([elem["confidence"] for elem in line_elements]) / len(line_elements)
        
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
            }
        }
    
    return text_lines


def perform_ocr(image: Image.Image, languages: List[str], recognition_level: str) -> Dict[str, Any]:
  
    if "th-TH" not in languages and "th" not in languages:
        languages = ["th-TH"] + languages
    
    ocr_result = process_image_with_vision(image, languages, recognition_level)
    
    recognized_text = ocr_result.get("text", "")
    
    document_type = classify_document_type(recognized_text, ocr_result.get("text_elements", []))
    
    text_lines = organize_text_elements_into_lines(ocr_result.get("text_elements", []))
    
    dimensions = ocr_result.get("dimensions", {"width": 0, "height": 0})
    dimensions["unit"] = "pixel"
    
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