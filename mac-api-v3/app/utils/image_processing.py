from PIL import Image
import io

def convert_to_supported_format(image: Image.Image) -> Image.Image:
    
    # Convert to RGB or RGBA to ensure compatibility with Vision Framework
    if image.mode not in ('RGB', 'RGBA'):
        image = image.convert('RGBA')
    
    # Check image size and resize if too large
    max_dimension = 4000  # Maximum recommended size (pixels)
    width, height = image.size
    
    if width > max_dimension or height > max_dimension:
        # Calculate resize ratio
        scale_ratio = min(max_dimension / width, max_dimension / height)
        new_width = int(width * scale_ratio)
        new_height = int(height * scale_ratio)
        
        # Resize image
        image = image.resize((new_width, new_height), Image.LANCZOS)
    
    return image