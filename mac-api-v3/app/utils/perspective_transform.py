import sys
import numpy as np
import tempfile
import os
import time
from PIL import Image, ImageDraw
from typing import List, Dict, Any, Tuple, Optional

def order_points(points: List[Dict[str, float]]) -> List[Dict[str, float]]:

    # Convert to numpy array for easier manipulation
    pts = np.zeros((4, 2), dtype="float32")
    for i, point in enumerate(points):
        pts[i] = [point["x"], point["y"]]
    
    # Sort points by x-coordinate
    xSorted = pts[np.argsort(pts[:, 0]), :]
    
    # Get leftmost and rightmost points
    leftMost = xSorted[:2, :]
    rightMost = xSorted[2:, :]
    
    # Sort leftmost points by y-coordinate
    leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
    topLeft, bottomLeft = leftMost
    
    # Sort rightmost points by y-coordinate
    rightMost = rightMost[np.argsort(rightMost[:, 1]), :]
    topRight, bottomRight = rightMost
    
    # Return in order: top-left, top-right, bottom-right, bottom-left
    return [
        {"x": float(topLeft[0]), "y": float(topLeft[1])},
        {"x": float(topRight[0]), "y": float(topRight[1])},
        {"x": float(bottomRight[0]), "y": float(bottomRight[1])},
        {"x": float(bottomLeft[0]), "y": float(bottomLeft[1])}
    ]

def calculate_destination_dimensions(src_points: List[Dict[str, float]]) -> Tuple[int, int]:
   
    # Calculate width as average of top and bottom sides
    width_top = np.sqrt(
        (src_points[1]["x"] - src_points[0]["x"])**2 + 
        (src_points[1]["y"] - src_points[0]["y"])**2
    )
    
    width_bottom = np.sqrt(
        (src_points[2]["x"] - src_points[3]["x"])**2 + 
        (src_points[2]["y"] - src_points[3]["y"])**2
    )
    
    # Calculate height as average of left and right sides
    height_left = np.sqrt(
        (src_points[3]["x"] - src_points[0]["x"])**2 + 
        (src_points[3]["y"] - src_points[0]["y"])**2
    )
    
    height_right = np.sqrt(
        (src_points[2]["x"] - src_points[1]["x"])**2 + 
        (src_points[2]["y"] - src_points[1]["y"])**2
    )
    
    # For a more natural result, use the average of each dimension
    avg_width = (width_top + width_bottom) / 2
    avg_height = (height_left + height_right) / 2
    
    # Round to integers
    width = max(10, int(avg_width))
    height = max(10, int(avg_height))
    
    # Calculate aspect ratio and ensure it's reasonable
    aspect_ratio = width / height
    
    # If aspect ratio is extreme, adjust to reasonable limits
    if aspect_ratio > 2.0:  # Too wide
        height = int(width / 2.0)
    elif aspect_ratio < 0.5:  # Too tall
        width = int(height / 2.0)
    
    return width, height

def perform_perspective_transform_macos(
    image: Image.Image,
    src_points: List[Dict[str, float]],
    width: Optional[int] = None,
    height: Optional[int] = None
) -> Dict[str, Any]:
   
    # Add debug print for troubleshooting
    print("Starting macOS perspective transform")
    start_time = time.time()
    temp_filename = None
    
    try:
        # Import macOS-specific libraries
        # These imports are inside the function to avoid errors on non-macOS systems
        import Foundation
        import Quartz
        from Cocoa import CIImage, CIContext, CIFilter
        
        print("Successfully imported macOS libraries")
        
        # Validate input points
        if len(src_points) != 4:
            raise ValueError("Exactly 4 points are required for perspective transformation")
        
        # Order points correctly
        ordered_points = order_points(src_points)
        print(f"Ordered points: {ordered_points}")
        
        # If width and height not specified, calculate optimal dimensions
        if width is None or height is None:
            calc_width, calc_height = calculate_destination_dimensions(ordered_points)
            width = width or calc_width
            height = height or calc_height
        
        # Ensure minimum dimensions
        width = max(width, 100)
        height = max(height, 100)
        print(f"Target dimensions: {width}x{height}")
        
        # Save image to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_filename = tmp.name
            image.save(temp_filename, 'PNG')
            print(f"Saved temporary image to {temp_filename}")
        
        # Load image using Foundation NSURL
        image_url = Foundation.NSURL.fileURLWithPath_(temp_filename)
        print("Created NSURL for image")
        
        # Load as CIImage
        ci_image = CIImage.imageWithContentsOfURL_(image_url)
        if ci_image is None:
            raise Exception("Failed to load image as CIImage")
        print("Loaded image as CIImage")
        
        # Get original image dimensions
        original_width = image.width
        original_height = image.height
        
        # Convert from PIL coordinates (top-left origin) to CI coordinates (bottom-left origin)
        src_top_left = Quartz.CIVector.vectorWithX_Y_(
            ordered_points[0]["x"], 
            original_height - ordered_points[0]["y"]
        )
        src_top_right = Quartz.CIVector.vectorWithX_Y_(
            ordered_points[1]["x"], 
            original_height - ordered_points[1]["y"]
        )
        src_bottom_right = Quartz.CIVector.vectorWithX_Y_(
            ordered_points[2]["x"], 
            original_height - ordered_points[2]["y"]
        )
        src_bottom_left = Quartz.CIVector.vectorWithX_Y_(
            ordered_points[3]["x"], 
            original_height - ordered_points[3]["y"]
        )
        print("Created CIVectors for corner points")
        
        # Create perspective correction filter
        perspective_filter = CIFilter.filterWithName_("CIPerspectiveCorrection")
        perspective_filter.setValue_forKey_(ci_image, "inputImage")
        perspective_filter.setValue_forKey_(src_top_left, "inputTopLeft")
        perspective_filter.setValue_forKey_(src_top_right, "inputTopRight")
        perspective_filter.setValue_forKey_(src_bottom_right, "inputBottomRight")
        perspective_filter.setValue_forKey_(src_bottom_left, "inputBottomLeft")
        print("Set up perspective correction filter")
        
        # Get the transformed image
        output_ci_image = perspective_filter.valueForKey_("outputImage")
        if output_ci_image is None:
            raise Exception("Failed to perform perspective correction")
        print("Got output CIImage from filter")
        
        # Create CIContext for rendering CIImage
        context = CIContext.contextWithOptions_(None)
        
        # Get extent of output image
        output_extent = output_ci_image.extent()
        
        # Convert CIImage to CGImage
        cg_image = context.createCGImage_fromRect_(output_ci_image, output_extent)
        if cg_image is None:
            raise Exception("Failed to convert CIImage to CGImage")
        print("Converted to CGImage")
        
        # Get actual dimensions of output image
        result_width = int(output_extent.size.width)
        result_height = int(output_extent.size.height)
        
        # Get bitmap representation of the image
        provider = Quartz.CGImageGetDataProvider(cg_image)
        data = Quartz.CGDataProviderCopyData(provider)
        buffer = memoryview(data)
        print("Got image data from CGImage")
        
        # Create PIL Image from buffer
        pil_image = Image.frombuffer(
            "RGBA", 
            (result_width, result_height), 
            buffer, 
            "raw", 
            "RGBA", 
            0, 
            1
        )
        print("Created PIL image from buffer")
        
        # Resize if specific dimensions requested
        if width is not None and height is not None and (width != result_width or height != result_height):
            pil_image = pil_image.resize((width, height), Image.LANCZOS)
            result_width = width
            result_height = height
            print(f"Resized image to {width}x{height}")
        
        # Calculate metrics
        dimensions = {"width": result_width, "height": result_height}
        fast_rate = (result_width * result_height) / 1000000
        rack_cooling_rate = (result_width + result_height) / 1000
        processing_time = time.time() - start_time
        
        print(f"macOS transform successful in {processing_time:.2f} seconds")
        
        return {
            "format": "PNG",
            "width": result_width,
            "height": result_height,
            "dimensions": dimensions,
            "fast_rate": fast_rate,
            "rack_cooling_rate": rack_cooling_rate,
            "processing_time": processing_time,
            "output_image": pil_image
        }
        
    except Exception as e:
        print(f"Error in macOS perspective transform: {str(e)}")
        # Handle errors
        return {
            "error": f"Error occurred: {str(e)}",
            "format": "PNG",
            "width": image.width,
            "height": image.height,
            "dimensions": {"width": image.width, "height": image.height},
            "fast_rate": (image.width * image.height) / 1000000,
            "rack_cooling_rate": (image.width + image.height) / 1000,
            "processing_time": time.time() - start_time,
            "output_image": image
        }
    finally:
        # Clean up temporary file
        if temp_filename and os.path.exists(temp_filename):
            try:
                os.unlink(temp_filename)
                print(f"Removed temporary file {temp_filename}")
            except Exception as e:
                print(f"Failed to remove temporary file: {str(e)}")

def perform_perspective_transform_opencv(
    image: Image.Image,
    src_points: List[Dict[str, float]],
    width: Optional[int] = None,
    height: Optional[int] = None
) -> Dict[str, Any]:
   
    print("Starting OpenCV perspective transform")
    start_time = time.time()
    
    try:
        # Try to import OpenCV
        try:
            import cv2
            print("Successfully imported OpenCV")
        except ImportError:
            raise ImportError("OpenCV (cv2) is required for this method")
        
        # Validate input points
        if len(src_points) != 4:
            raise ValueError("Exactly 4 points are required for perspective transformation")
        
        # Convert PIL image to OpenCV format
        img_cv = np.array(image)
        if len(img_cv.shape) == 3 and img_cv.shape[2] == 4:  # If RGBA
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGBA2BGR)
        elif len(img_cv.shape) == 3 and img_cv.shape[2] == 3:  # If RGB
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
        print(f"Converted PIL image to OpenCV format: shape={img_cv.shape}")
        
        # Order points correctly
        ordered_pts = order_points(src_points)
        print(f"Ordered points: {ordered_pts}")
        
        # Extract source points as numpy array
        src = np.array([
            [ordered_pts[0]["x"], ordered_pts[0]["y"]],
            [ordered_pts[1]["x"], ordered_pts[1]["y"]],
            [ordered_pts[2]["x"], ordered_pts[2]["y"]],
            [ordered_pts[3]["x"], ordered_pts[3]["y"]]
        ], dtype=np.float32)
        
        # Calculate dimensions if not provided
        if width is None or height is None:
            calc_width, calc_height = calculate_destination_dimensions(ordered_pts)
            width = width or calc_width
            height = height or calc_height
        
        # Ensure minimum dimensions
        width = max(width, 10)
        height = max(height, 10)
        print(f"Target dimensions: {width}x{height}")
        
        # Set destination points for a rectangle of the desired dimensions
        dst = np.array([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ], dtype=np.float32)
        
        # Calculate perspective transform matrix
        M = cv2.getPerspectiveTransform(src, dst)
        print("Calculated perspective transform matrix")
        
        # Apply transformation
        warped = cv2.warpPerspective(img_cv, M, (width, height))
        print(f"Applied perspective transform: result shape={warped.shape}")
        
        # Convert back to PIL image - make sure we handle RGBA if needed
        if image.mode == 'RGBA':
            # Convert BGR to BGRA
            warped_rgba = cv2.cvtColor(warped, cv2.COLOR_BGR2BGRA)
            # Set alpha channel to max
            warped_rgba[:, :, 3] = 255
            result_image = Image.fromarray(cv2.cvtColor(warped_rgba, cv2.COLOR_BGRA2RGBA))
        else:
            result_image = Image.fromarray(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB))
        print("Converted result back to PIL image")
        
        # Calculate metrics
        dimensions = {"width": width, "height": height}
        fast_rate = (width * height) / 1000000
        rack_cooling_rate = (width + height) / 1000
        processing_time = time.time() - start_time
        
        print(f"OpenCV transform successful in {processing_time:.2f} seconds")
        
        return {
            "format": "PNG",
            "width": width,
            "height": height,
            "dimensions": dimensions,
            "fast_rate": fast_rate,
            "rack_cooling_rate": rack_cooling_rate,
            "processing_time": processing_time,
            "output_image": result_image
        }
        
    except Exception as e:
        print(f"Error in OpenCV perspective transform: {str(e)}")
        # Handle errors
        return {
            "error": f"Error occurred: {str(e)}",
            "format": "PNG",
            "width": image.width,
            "height": image.height,
            "dimensions": {"width": image.width, "height": image.height},
            "fast_rate": (image.width * image.height) / 1000000,
            "rack_cooling_rate": (image.width + image.height) / 1000,
            "processing_time": time.time() - start_time,
            "output_image": image
        }

def perform_perspective_transform(
    image: Image.Image,
    src_points: List[Dict[str, float]],
    width: Optional[int] = None,
    height: Optional[int] = None
) -> Dict[str, Any]:
  
    print(f"Starting perspective transform on platform: {sys.platform}")
    print(f"Input image size: {image.width}x{image.height}, mode: {image.mode}")
    print(f"Source points: {src_points}")
    print(f"Requested dimensions: width={width}, height={height}")
    
    # Use macOS implementation if on macOS, otherwise use OpenCV
    if sys.platform == "darwin":
        try:
            print("Attempting macOS implementation...")
            return perform_perspective_transform_macos(image, src_points, width, height)
        except Exception as e:
            print(f"macOS implementation failed: {e}, falling back to OpenCV")
            return perform_perspective_transform_opencv(image, src_points, width, height)
    else:
        print("Not on macOS, using OpenCV implementation")
        return perform_perspective_transform_opencv(image, src_points, width, height)

def visualize_perspective_points(image: Image.Image, points: List[Dict[str, float]]) -> Image.Image:
    
    print("Creating visualization of perspective points")
    
    # Create a copy of the image to draw on
    result = image.copy()
    draw = ImageDraw.Draw(result)
    
    # Order points
    ordered_points = order_points(points)
    
    # Draw points
    for i, point in enumerate(ordered_points):
        x, y = point["x"], point["y"]
        point_size = 10
        
        # Different colors for each corner
        colors = [
            (255, 0, 0, 200),    # Red - Top Left (1)
            (0, 255, 0, 200),    # Green - Top Right (2)
            (0, 0, 255, 200),    # Blue - Bottom Right (3)
            (255, 255, 0, 200)   # Yellow - Bottom Left (4)
        ]
        
        # Draw circle for each point
        draw.ellipse(
            [(x - point_size, y - point_size), (x + point_size, y + point_size)],
            fill=colors[i]
        )
        
        # Draw point number with labels
        labels = ["1:TL", "2:TR", "3:BR", "4:BL"]
        draw.text((x + 15, y - 15), labels[i], fill=colors[i][:3])
    
    # Draw lines connecting the points to show the quadrilateral
    for i in range(4):
        start = (ordered_points[i]["x"], ordered_points[i]["y"])
        end = (ordered_points[(i + 1) % 4]["x"], ordered_points[(i + 1) % 4]["y"])
        draw.line([start, end], fill=(255, 0, 0, 200), width=2)
    
    # Add legend explaining the colors
    draw.text((10, 10), "1:TL = Top Left (Red)", fill=(255, 0, 0))
    draw.text((10, 30), "2:TR = Top Right (Green)", fill=(0, 255, 0))
    draw.text((10, 50), "3:BR = Bottom Right (Blue)", fill=(0, 0, 255))
    draw.text((10, 70), "4:BL = Bottom Left (Yellow)", fill=(255, 255, 0))
    
    print("Visualization created successfully")
    return result

def detect_rectangle(image: Image.Image) -> List[Dict[str, float]]:
    
    print("Attempting to detect rectangle in image")
    
    try:
        import cv2
        print("Successfully imported OpenCV for rectangle detection")
    except ImportError:
        print("OpenCV not available for rectangle detection")
        raise ImportError("OpenCV (cv2) is required for rectangle detection")
    
    try:
        # Convert PIL image to OpenCV format
        img_cv = np.array(image)
        if len(img_cv.shape) == 3 and img_cv.shape[2] == 4:  # If RGBA
            img_cv_bgr = cv2.cvtColor(img_cv, cv2.COLOR_RGBA2BGR)
        elif len(img_cv.shape) == 3 and img_cv.shape[2] == 3:  # If RGB
            img_cv_bgr = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
        else:
            img_cv_bgr = cv2.cvtColor(img_cv, cv2.COLOR_GRAY2BGR)
        print(f"Converted PIL image to OpenCV format: shape={img_cv_bgr.shape}")
        
        # Convert to grayscale for processing
        img_cv_gray = cv2.cvtColor(img_cv_bgr, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            img_cv_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply morphological operations
        kernel = np.ones((3, 3), np.uint8)
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
        
        # Edge detection
        edges1 = cv2.Canny(img_cv_gray, 50, 150)
        edges2 = cv2.Canny(morph, 50, 150)
        edges = cv2.bitwise_or(edges1, edges2)
        
        # Dilate edges
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"Found {len(contours)} contours")
        
        # Filter by minimum area
        min_area = image.width * image.height * 0.05
        contours = [c for c in contours if cv2.contourArea(c) > min_area]
        print(f"After filtering: {len(contours)} contours")
        
        # Sort contours by area
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        # Initialize result
        rectangle_points = None
        
        # Find the best rectangular approximation
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            if len(approx) == 4:
                rectangle_points = approx
                print("Found exact 4-point rectangle")
                break
            elif len(approx) > 4 and len(approx) <= 6:
                rect = cv2.minAreaRect(contour)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                rectangle_points = box
                print(f"Found approximate rectangle ({len(approx)} points, using minimum area rectangle)")
                break
        
        # Fallback if no rectangle found
        if rectangle_points is None and contours:
            rect = cv2.minAreaRect(contours[0])
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            rectangle_points = box
            print("Used minimum area rectangle of largest contour")
        
        # Final fallback
        if rectangle_points is None:
            h, w = img_cv_gray.shape
            rectangle_points = np.array([
                [[0, 0]],
                [[w-1, 0]],
                [[w-1, h-1]],
                [[0, h-1]]
            ])
            print("No contours found, using image boundaries")
        
        # Convert to our format
        points = []
        for point in rectangle_points:
            if len(point.shape) > 1:
                points.append({"x": float(point[0][0]), "y": float(point[0][1])})
            else:
                points.append({"x": float(point[0]), "y": float(point[1])})
        
        # Order points correctly
        ordered_points = order_points(points)
        print(f"Final rectangle points: {ordered_points}")
        return ordered_points
        
    except Exception as e:
        print(f"Rectangle detection failed: {e}")
        # Return the four corners of the image as fallback
        w, h = image.size
        points = [
            {"x": 0, "y": 0},
            {"x": w-1, "y": 0},
            {"x": w-1, "y": h-1},
            {"x": 0, "y": h-1}
        ]
        print(f"Using image corners as fallback: {points}")
        return points