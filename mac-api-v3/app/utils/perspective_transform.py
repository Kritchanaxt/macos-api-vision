
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
    
    # Sort points by their position to ensure correct order: top-left, top-right, bottom-right, bottom-left
    # First sort by y-coordinate (top to bottom)
    src_points_array = src_points_array[np.argsort(src_points_array[:, 1])]
    
    # Now the first two points are the top points, sort them by x-coordinate
    if src_points_array[0][0] > src_points_array[1][0]:
        src_points_array[[0, 1]] = src_points_array[[1, 0]]
    
    # The last two points are the bottom points, sort them by x-coordinate (right to left)
    if src_points_array[2][0] < src_points_array[3][0]:
        src_points_array[[2, 3]] = src_points_array[[3, 2]]
    
    # If width and height are not provided, calculate from max dimensions of source points
    if width is None or height is None:
        # Find the max width and height
        width_top = np.sqrt(((src_points_array[1][0] - src_points_array[0][0]) ** 2) + 
                           ((src_points_array[1][1] - src_points_array[0][1]) ** 2))
        width_bottom = np.sqrt(((src_points_array[2][0] - src_points_array[3][0]) ** 2) + 
                              ((src_points_array[2][1] - src_points_array[3][1]) ** 2))
        max_width = int(max(width_top, width_bottom))
        
        height_left = np.sqrt(((src_points_array[3][0] - src_points_array[0][0]) ** 2) + 
                             ((src_points_array[3][1] - src_points_array[0][1]) ** 2))
        height_right = np.sqrt(((src_points_array[2][0] - src_points_array[1][0]) ** 2) + 
                              ((src_points_array[2][1] - src_points_array[1][1]) ** 2))
        max_height = int(max(height_left, height_right))
        
        if width is None:
            width = max_width
        if height is None:
            height = max_height
    
    # Define destination points for a rectangle
    dst_points = np.array([
        [0, 0],              # Top-left
        [width - 1, 0],      # Top-right
        [width - 1, height - 1],  # Bottom-right
        [0, height - 1]      # Bottom-left
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