
from PIL import Image, ImageDraw
import numpy as np
import cv2
import os
import uuid
from datetime import datetime
from typing import List, Tuple, Dict, Any

def perform_perspective_transform(
    image: Image.Image,
    src_points: List[Dict[str, float]],
    width: int = None,
    height: int = None
) -> Dict[str, Any]:
    """
    Perform perspective transformation on an image based on 4 source points.
    
    Args:
        image: PIL Image object
        src_points: List of 4 points in format [{"x": x1, "y": y1}, {"x": x2, "y": y2}, ...]
        width: Optional desired width of output image (if None, calculated from points)
        height: Optional desired height of output image (if None, calculated from points)
        
    Returns:
        Dictionary containing transformation results
    """
    # Start timing
    import time
    start_time = time.time()
    
    # Convert PIL Image to OpenCV format
    img_cv = np.array(image)
    if img_cv.shape[2] == 4:  # If RGBA
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGBA2BGR)
    else:
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
    
    # Extract source points as np.array
    src_points_array = np.array([
        [point["x"], point["y"]] for point in src_points
    ], dtype=np.float32)
    
    # Verify we have 4 points
    if len(src_points_array) != 4:
        raise ValueError("Exactly 4 source points are required for perspective transformation")
    
    # If width and height are not provided, calculate from max dimensions of source points
    if width is None or height is None:
        # Calculate width and height from the bounding rectangle of the destination quadrilateral
        x_min = min(p["x"] for p in src_points)
        x_max = max(p["x"] for p in src_points)
        y_min = min(p["y"] for p in src_points)
        y_max = max(p["y"] for p in src_points)
        
        if width is None:
            width = int(x_max - x_min)
        if height is None:
            height = int(y_max - y_min)
    
    # Define destination points for a rectangle
    dst_points = np.array([
        [0, 0],
        [width, 0],
        [width, height],
        [0, height]
    ], dtype=np.float32)
    
    # Compute the perspective transform matrix
    matrix = cv2.getPerspectiveTransform(src_points_array, dst_points)
    
    # Apply the perspective transformation
    transformed_img = cv2.warpPerspective(img_cv, matrix, (width, height))
    
    # Convert back to PIL Image
    result_image = Image.fromarray(cv2.cvtColor(transformed_img, cv2.COLOR_BGR2RGB))
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Get image dimensions for response
    dimensions = {
        "width": result_image.width,
        "height": result_image.height
    }
    
    # Calculate fast rate and rack cooling rate
    fast_rate = (dimensions["width"] * dimensions["height"]) / 1000000
    rack_cooling_rate = (dimensions["width"] + dimensions["height"]) / 1000
    
    # Return results
    result = {
        "format": result_image.format if result_image.format else "PNG",
        "width": dimensions["width"],
        "height": dimensions["height"],
        "dimensions": dimensions,
        "fast_rate": fast_rate,
        "rack_cooling_rate": rack_cooling_rate,
        "processing_time": processing_time,
        "output_image": result_image
    }
    
    return result

def visualize_perspective_points(
    image: Image.Image,
    points: List[Dict[str, float]]
) -> Image.Image:
    """
    Creates a visualization of the input image with selected corner points
    
    Args:
        image: PIL Image object
        points: List of 4 points in format [{"x": x1, "y": y1}, {"x": x2, "y": y2}, ...]
        
    Returns:
        PIL Image with visualization markers
    """
    # Create a copy of the image to draw on
    visualization = image.copy()
    draw = ImageDraw.Draw(visualization)
    
    # Draw points
    point_radius = max(5, min(image.width, image.height) // 100)
    for i, point in enumerate(points):
        x, y = point["x"], point["y"]
        
        # Draw circle for each point
        draw.ellipse(
            [(x - point_radius, y - point_radius), 
             (x + point_radius, y + point_radius)], 
            fill=(255, 0, 0, 255)
        )
        
        # Draw point number
        draw.text((x + point_radius + 5, y - point_radius - 5), 
                  f"{i+1}", fill=(255, 0, 0, 255))
    
    # Draw lines connecting the points in order
    for i in range(4):
        start = (points[i]["x"], points[i]["y"])
        end = (points[(i + 1) % 4]["x"], points[(i + 1) % 4]["y"])
        draw.line([start, end], fill=(0, 255, 0, 255), width=2)
    
    return visualization