from PIL import Image
from typing import Dict, Any, Tuple

def get_image_dimensions(image: Image.Image) -> Dict[str, int]:

    width, height = image.size
    return {
        "width": width,
        "height": height
    }

def calculate_fast_rate(width: int, height: int) -> float:
    return (width * height) / 1000000

def calculate_rack_cooling_rate(width: int, height: int, face_count: int = 0) -> float:
    return (width + height) * (1 + face_count/10) / 1000