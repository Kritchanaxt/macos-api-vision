from app.ocr.vision_ocr import process_image_with_vision
from typing import List, Dict, Any
from PIL import Image

def perform_ocr(image: Image.Image, languages: List[str], recognition_level: str) -> Dict[str, Any]:
  
    # Check if Thai language is in the list
    if "th-TH" not in languages and "th" not in languages:
        # Add Thai support automatically
        languages = ["th-TH"] + languages
    
    # Call OCR function from Vision Framework
    ocr_result = process_image_with_vision(image, languages, recognition_level)
    
    return ocr_result