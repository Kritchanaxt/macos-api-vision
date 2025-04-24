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
    height: int = None,
    refine_corners: bool = True,
    interpolation_mode: int = cv2.INTER_LINEAR
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
    
    # Refine corners for more accurate transformation
    if refine_corners:
        src_points_array = refine_corner_points(img_cv, src_points_array)
    
    # Sort points - top-left, top-right, bottom-right, bottom-left
    src_points_array = sort_points(src_points_array)
    
    # If width and height are not provided, calculate optimal dimensions
    if width is None or height is None:
        calculated_width, calculated_height = calculate_optimal_dimensions(src_points_array)
        
        if width is None:
            width = calculated_width
        if height is None:
            height = calculated_height
    
    # Define destination points for a rectangle
    dst_points = np.array([
        [0, 0],                 # Top-left
        [width - 1, 0],         # Top-right
        [width - 1, height - 1],# Bottom-right
        [0, height - 1]         # Bottom-left
    ], dtype=np.float32)
    
    # Compute the perspective transform matrix
    matrix = cv2.getPerspectiveTransform(src_points_array, dst_points)
    
    # Apply the perspective transformation
    transformed_img = cv2.warpPerspective(
        img_cv, 
        matrix, 
        (width, height), 
        flags=interpolation_mode,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255)  # White border
    )
    
    # Convert back to PIL Image
    result_image = Image.fromarray(cv2.cvtColor(transformed_img, cv2.COLOR_BGR2RGB))
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Get image dimensions for response
    dimensions = {
        "width": result_image.width,
        "height": result_image.height
    }
    
    # Calculate metrics
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

def refine_corner_points(image: np.ndarray, points: np.ndarray) -> np.ndarray:
    
    # Convert to grayscale for corner detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Parameters for cornerSubPix
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    window_size = 11
    
    # Refine each point
    refined_points = np.copy(points)
    
    for i, point in enumerate(points):
        # Define a region around the point
        x, y = int(point[0]), int(point[1])
        
        # Skip if point is outside image boundaries
        if x < 0 or y < 0 or x >= image.shape[1] or y >= image.shape[0]:
            continue
            
        # Extract region for corner detection
        half_size = window_size // 2
        roi_x1 = max(0, x - half_size)
        roi_y1 = max(0, y - half_size)
        roi_x2 = min(image.shape[1], x + half_size + 1)
        roi_y2 = min(image.shape[0], y + half_size + 1)
        
        # Skip if ROI is too small
        if roi_x2 - roi_x1 < 3 or roi_y2 - roi_y1 < 3:
            continue
            
        # Create mask for the ROI and detect corners
        roi = gray[roi_y1:roi_y2, roi_x1:roi_x2]
        corners = cv2.cornerHarris(roi, 2, 3, 0.04)
        
        # Threshold for corner detection
        corners = cv2.dilate(corners, None)
        threshold = 0.01 * corners.max()
        corner_positions = np.where(corners > threshold)
        
        # If corners found, use the closest one
        if len(corner_positions[0]) > 0:
            corner_y = corner_positions[0] + roi_y1
            corner_x = corner_positions[1] + roi_x1
            
            # Find closest corner to original point
            distances = np.sqrt((corner_y - y) ** 2 + (corner_x - x) ** 2)
            closest_idx = np.argmin(distances)
            
            # Use the closest corner if it's within reasonable distance
            if distances[closest_idx] < window_size // 2:
                refined_points[i] = [corner_x[closest_idx], corner_y[closest_idx]]
    
    # Further refine with sub-pixel accuracy
    try:
        cv2.cornerSubPix(gray, refined_points, (5, 5), (-1, -1), criteria)
    except Exception:
        # If cornerSubPix fails, use original refined points
        pass
    
    return refined_points

def sort_points(points: np.ndarray) -> np.ndarray:
    
    # Calculate center point
    center = np.mean(points, axis=0)
    
    # Calculate angles from center
    angles = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
    
    # Sort by angle (counterclockwise from right)
    sorted_indices = np.argsort(angles)
    sorted_points = points[sorted_indices]
    
    # Rotate to ensure top-left is first
    # Find point with minimum sum of coordinates (likely top-left)
    sums = np.sum(sorted_points, axis=1)
    min_idx = np.argmin(sums)
    
    # Rotate array so top-left is first
    sorted_points = np.roll(sorted_points, -min_idx, axis=0)
    
    return sorted_points

def calculate_optimal_dimensions(points: np.ndarray) -> Tuple[int, int]:
  
    # Calculate distances between points
    width_top = np.linalg.norm(points[1] - points[0])
    width_bottom = np.linalg.norm(points[2] - points[3])
    height_left = np.linalg.norm(points[3] - points[0])
    height_right = np.linalg.norm(points[2] - points[1])
    
    # Use average dimensions
    width = int(round((width_top + width_bottom) / 2))
    height = int(round((height_left + height_right) / 2))
    
    # Ensure minimum dimensions
    width = max(width, 10)
    height = max(height, 10)
    
    return width, height

def visualize_perspective_points(
    image: Image.Image,
    points: List[Dict[str, float]],
    add_labels: bool = True,
    add_numbers: bool = True,
    draw_grid: bool = True
) -> Image.Image:
    
    # Create a copy of the image to draw on
    visualization = image.copy()
    draw = ImageDraw.Draw(visualization)
    
    # Get image dimensions
    img_width, img_height = image.size
    
    # Draw grid for visualization
    if draw_grid:
        # Draw horizontal lines
        for y in range(0, img_height, img_height // 10):
            draw.line([(0, y), (img_width, y)], fill=(0, 0, 255, 64), width=1)
        
        # Draw vertical lines
        for x in range(0, img_width, img_width // 10):
            draw.line([(x, 0), (x, img_height)], fill=(0, 0, 255, 64), width=1)
    
    # Extract points as array
    points_array = np.array([[p["x"], p["y"]] for p in points])
    
    # Sort points
    if len(points_array) == 4:
        points_array = sort_points(points_array)
    
    # Draw lines connecting the points
    for i in range(len(points_array)):
        # Draw line to next point (wrap around to first for last point)
        start = (points_array[i][0], points_array[i][1])
        end = (points_array[(i + 1) % len(points_array)][0], points_array[(i + 1) % len(points_array)][1])
        draw.line([start, end], fill=(0, 255, 0, 255), width=2)
    
    # Draw points
    point_radius = max(5, min(img_width, img_height) // 100)
    for i, point in enumerate(points_array):
        x, y = point[0], point[1]
        
        # Draw circle for point
        draw.ellipse(
            [(x - point_radius, y - point_radius), 
             (x + point_radius, y + point_radius)], 
            fill=(255, 0, 0, 255),
            outline=(0, 0, 0, 255)
        )
        
        # Draw point number
        if add_numbers:
            draw.text((x + point_radius + 5, y - point_radius - 5), 
                      f"{i+1}", fill=(255, 0, 0, 255))
    
    # Add labels if requested
    if add_labels and len(points_array) == 4:
        labels = ["Top-Left", "Top-Right", "Bottom-Right", "Bottom-Left"]
        for i, (point, label) in enumerate(zip(points_array, labels)):
            x, y = point[0], point[1]
            offset_x = 10 if x < img_width/2 else -60
            offset_y = 10 if y < img_height/2 else -20
            
            draw.text((x + offset_x, y + offset_y), label, fill=(0, 0, 0, 255))
    
    return visualization