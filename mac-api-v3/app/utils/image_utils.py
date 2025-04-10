from PIL import Image
from typing import Dict, Any, Tuple

def get_image_dimensions(image: Image.Image) -> Dict[str, int]:
    """
    Get dimensions of an image.
    
    Args:
        image: PIL Image object
        
    Returns:
        Dictionary with width and height
    """
    width, height = image.size
    return {
        "width": width,
        "height": height
    }

def calculate_fast_rate(width: int, height: int) -> float:
    """
    Calculate Fast Rate based on image dimensions.
    Fast Rate is defined as (width * height) / 1000000
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        
    Returns:
        Fast Rate value
    """
    return (width * height) / 1000000

def calculate_rack_cooling_rate(width: int, height: int, face_count: int = 0) -> float:
    """
    Calculate Rack Cooling Rate based on image dimensions and face count.
    Rack Cooling Rate is defined as (width + height) * (1 + face_count/10) / 1000
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        face_count: Number of faces detected (default: 0)
        
    Returns:
        Rack Cooling Rate value
    """
    return (width + height) * (1 + face_count/10) / 1000