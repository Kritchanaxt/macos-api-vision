import numpy as np
import cv2
from PIL import Image, ImageDraw
import time
from typing import List, Dict, Tuple, Optional, Any
from app.utils.image_utils import get_image_dimensions, calculate_fast_rate, calculate_rack_cooling_rate

def order_points(pts: np.ndarray) -> np.ndarray:
    # Initialize empty array
    rect = np.zeros((4, 2), dtype="float32")
    
    # Sum the (x, y) coordinates
    s = pts.sum(axis=1)
    # Top-left point will have the smallest sum
    rect[0] = pts[np.argmin(s)]
    # Bottom-right point will have the largest sum
    rect[2] = pts[np.argmax(s)]
    
    # Compute the difference between coordinates
    diff = np.diff(pts, axis=1)
    # Top-right point will have the smallest difference
    rect[1] = pts[np.argmin(diff)]
    # Bottom-left point will have the largest difference
    rect[3] = pts[np.argmax(diff)]
    
    return rect

def four_point_transform(image: Image.Image, pts: List[Dict[str, float]]) -> Tuple[Image.Image, Dict[str, Any]]:

    start_time = time.time()
    
    # Convert PIL Image to NumPy array
    img_np = np.array(image)
    
    # Convert coordinate list to NumPy array
    # These are normalized coordinates (0-1), convert to pixel coordinates
    points = np.array([[p["x"] * image.width, (1-p["y"]) * image.height] for p in pts], dtype="float32")
    
    # Create a copy of the original image to draw corner points
    debug_image = image.copy()
    draw = ImageDraw.Draw(debug_image)
    
    # Draw corner points on debug image
    point_radius = 8
    for i, (x, y) in enumerate(points):
        color = [
            (255, 0, 0),    # Top-left: Red
            (0, 255, 0),    # Top-right: Green
            (0, 0, 255),    # Bottom-right: Blue
            (255, 255, 0)   # Bottom-left: Yellow
        ][i % 4]
        draw.ellipse((x - point_radius, y - point_radius, x + point_radius, y + point_radius), fill=color)
        draw.text((x + point_radius, y + point_radius), f"P{i+1}", fill=color)
    
    # Order points in correct sequence for perspective transform
    rect = order_points(points)
    
    # Draw ordered corner points on debug image
    for i, (x, y) in enumerate(rect):
        color = (255, 255, 255)  # White for ordered points
        draw.ellipse((x - point_radius/2, y - point_radius/2, x + point_radius/2, y + point_radius/2), fill=color)
        draw.text((x, y), f"O{i+1}", fill=color)
    
    # Size of the transformed image
    (tl, tr, br, bl) = rect
    
    # Calculate width of new image
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    
    # Calculate height of new image
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    
    # Ensure minimum dimensions
    maxWidth = max(maxWidth, 100)
    maxHeight = max(maxHeight, 100)
    
    # Create destination coordinates for transformation
    dst = np.array([
        [0, 0],                      # Top-left corner
        [maxWidth - 1, 0],           # Top-right corner
        [maxWidth - 1, maxHeight - 1], # Bottom-right corner
        [0, maxHeight - 1]           # Bottom-left corner
    ], dtype="float32")
    
    # Calculate perspective transformation matrix
    M = cv2.getPerspectiveTransform(rect, dst)
    
    # Transform the image
    warped = cv2.warpPerspective(img_np, M, (maxWidth, maxHeight))
    
    # Convert back to PIL Image
    warped_pil = Image.fromarray(warped)
    
    # Get dimensions of transformed image
    dimensions = get_image_dimensions(warped_pil)
    
    # Calculate rates
    fast_rate = calculate_fast_rate(dimensions["width"], dimensions["height"])
    rack_cooling_rate = calculate_rack_cooling_rate(dimensions["width"], dimensions["height"])
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Prepare metadata
    metadata = {
        "dimensions": dimensions,
        "fast_rate": fast_rate,
        "rack_cooling_rate": rack_cooling_rate,
        "processing_time": processing_time,
        "debug_image": debug_image  # Include debug image in metadata
    }
    
    return warped_pil, metadata

def wrap_card_perspective(image: Image.Image, corners: List[Dict[str, float]]) -> Tuple[Optional[Image.Image], Dict[str, Any]]:
   
    start_time = time.time()
    
    try:
        # Add some validation for corner points
        if len(corners) != 4:
            raise ValueError(f"Expected 4 corner points, but got {len(corners)}")
        
        # Check if coordinates are within valid range (0-1)
        for i, corner in enumerate(corners):
            if not (0 <= corner["x"] <= 1 and 0 <= corner["y"] <= 1):
                # Clamp to valid range
                corners[i]["x"] = max(0, min(1, corner["x"]))
                corners[i]["y"] = max(0, min(1, corner["y"]))
        
        # Perform perspective transformation
        warped, metadata = four_point_transform(image, corners)
        
        # Update processing time to include the full function execution
        metadata["processing_time"] = time.time() - start_time
        
        return warped, metadata
    except Exception as e:
        print(f"Error adjusting perspective: {str(e)}")
        # Return original image dimensions in error case
        dimensions = get_image_dimensions(image)
        metadata = {
            "error": str(e),
            "dimensions": dimensions,
            "fast_rate": calculate_fast_rate(dimensions["width"], dimensions["height"]),
            "rack_cooling_rate": calculate_rack_cooling_rate(dimensions["width"], dimensions["height"]),
            "processing_time": time.time() - start_time
        }
        return None, metadata