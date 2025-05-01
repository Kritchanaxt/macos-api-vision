from PIL import Image
from typing import Dict, Any, Tuple, Union
from Foundation import NSSize

def get_image_dimensions(image: Union[Image.Image, NSSize]) -> Dict[str, Any]:
    """
    Get image dimensions from PIL Image or NSSize
    
    Args:
        image: PIL Image or NSSize object
    
    Returns:
        Dictionary with width, height and unit
    """
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
    """
    Calculate fast rate based on image dimensions
    
    Args:
        width: Image width
        height: Image height
        
    Returns:
        Fast rate value
    """
    return (width * height) / 1000000.0

def calculate_rack_cooling_rate(width: float, height: float, face_count: int = 0) -> float:
    """
    Calculate rack cooling rate based on image dimensions
    
    Args:
        width: Image width
        height: Image height
        face_count: Number of faces detected (optional)
        
    Returns:
        Rack cooling rate value
    """
    return (width + height) * (1 + face_count/10) / 1000.0