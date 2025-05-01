from PIL import Image
from typing import Dict, Any, Tuple, Union
from Foundation import NSSize

def get_image_dimensions(image: Union[Image.Image, NSSize]) -> Dict[str, Any]:
    
    if isinstance(image, Image.Image):
        width, height = image.size
    else:  # Assume NSSize
        width = image.width
        height = image.height
        
    return {
        "width": width,
        "height": height,
        "unit": "pixel"
    }

def calculate_fast_rate(width: float, height: float) -> float:
    return (width * height) / 1000000.0

def calculate_rack_cooling_rate(width: float, height: float, face_count: int = 0) -> float:
    return (width + height) * (1 + face_count/10) / 1000.0