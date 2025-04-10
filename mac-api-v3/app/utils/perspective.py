import numpy as np
import cv2
from PIL import Image
from typing import List, Dict, Tuple, Optional

def order_points(pts: np.ndarray) -> np.ndarray:
   
    # Initialize empty array
    rect = np.zeros((4, 2), dtype="float32")
    
    # Top-left point will have the smallest sum of coordinates
    # Bottom-right point will have the largest sum of coordinates
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # Top-right point will have the smallest difference of coordinates
    # Bottom-left point will have the largest difference of coordinates
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect

def four_point_transform(image: Image.Image, pts: List[Dict[str, float]]) -> Image.Image:
   
    # Convert PIL Image to NumPy array
    img_np = np.array(image)
    
    # Convert coordinate list to NumPy array
    points = np.array([[p["x"] * image.width, p["y"] * image.height] for p in pts], dtype="float32")
    
    # Order points
    rect = order_points(points)
    
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
    
    # Create destination coordinates for transformation
    dst = np.array([
        [0, 0],  # Top-left corner
        [maxWidth - 1, 0],  # Top-right corner
        [maxWidth - 1, maxHeight - 1],  # Bottom-right corner
        [0, maxHeight - 1]  # Bottom-left corner
    ], dtype="float32")
    
    # Calculate perspective transformation matrix
    M = cv2.getPerspectiveTransform(rect, dst)
    
    # Transform the image
    warped = cv2.warpPerspective(img_np, M, (maxWidth, maxHeight))
    
    # Convert back to PIL Image
    warped_pil = Image.fromarray(warped)
    
    return warped_pil

def wrap_card_perspective(image: Image.Image, corners: List[Dict[str, float]]) -> Optional[Image.Image]:
   
    try:
        # Perform perspective transformation
        warped = four_point_transform(image, corners)
        return warped
    except Exception as e:
        print(f"Error adjusting perspective: {str(e)}")
        return None