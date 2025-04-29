import numpy as np
import tempfile
import os
import time
from PIL import Image, ImageDraw
from typing import List, Dict, Any, Tuple, Optional


def order_points(points: List[Dict[str, float]]) -> List[Dict[str, float]]:
    pts = np.zeros((4, 2), dtype="float32")
    for i, point in enumerate(points):
        pts[i] = [point["x"], point["y"]]
    
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1)
    
    rect = np.zeros((4, 2), dtype="float32")
    rect[0] = pts[np.argmin(s)]  # Top-left: smallest sum
    rect[2] = pts[np.argmax(s)]  # Bottom-right: largest sum
    rect[1] = pts[np.argmin(d)]  # Top-right: smallest diff
    rect[3] = pts[np.argmax(d)]  # Bottom-left: largest diff
    
    result = []
    for i in range(4):
        result.append({
            "x": float(rect[i, 0]),
            "y": float(rect[i, 1])
        })
    
    return result


def calculate_destination_dimensions(src_points: List[Dict[str, float]]) -> Tuple[int, int]:
    width_top = np.sqrt(
        (src_points[1]["x"] - src_points[0]["x"])**2 + 
        (src_points[1]["y"] - src_points[0]["y"])**2
    )
    
    width_bottom = np.sqrt(
        (src_points[2]["x"] - src_points[3]["x"])**2 + 
        (src_points[2]["y"] - src_points[3]["y"])**2
    )
    
    height_left = np.sqrt(
        (src_points[3]["x"] - src_points[0]["x"])**2 + 
        (src_points[3]["y"] - src_points[0]["y"])**2
    )
    
    height_right = np.sqrt(
        (src_points[2]["x"] - src_points[1]["x"])**2 + 
        (src_points[2]["y"] - src_points[1]["y"])**2
    )
    
    width = int((width_top + width_bottom) / 2)
    height = int((height_left + height_right) / 2)
    
    width = max(width, 100)
    height = max(height, 100)
    
    target_aspect = 1.586
    current_aspect = width / height
    
    if abs(current_aspect - target_aspect) > 0.3:
        if current_aspect > target_aspect:
            height = int(width / target_aspect)
        else:
            width = int(height * target_aspect)
    
    return width, height


def calculate_metrics(width: int, height: int, processing_time: float) -> Dict[str, Any]:
    return {
        "format": "PNG",
        "width": width,
        "height": height,
        "dimensions": {"width": width, "height": height},
        "fast_rate": (width * height) / 1000000,
        "rack_cooling_rate": (width + height) / 1000,
        "processing_time": processing_time
    }


def handle_transform_error(e: Exception, image: Image.Image, start_time: float) -> Dict[str, Any]:
    print(f"Error in perspective transform: {str(e)}")
    metrics = calculate_metrics(image.width, image.height, time.time() - start_time)
    metrics["error"] = f"Error occurred: {str(e)}"
    metrics["output_image"] = image
    return metrics


def perform_perspective_transform_macos(
    image: Image.Image,
    src_points: List[Dict[str, float]],
    width: Optional[int] = None,
    height: Optional[int] = None
) -> Dict[str, Any]:
    print("Starting perspective transform with Apple Accelerate API")
    start_time = time.time()
    
    try:
        # Validate input points
        if len(src_points) != 4:
            raise ValueError("Exactly 4 points are required for perspective transformation")
        
        # Order points correctly (top-left, top-right, bottom-right, bottom-left)
        ordered_points = order_points(src_points)
        
        # If width and height not specified, calculate optimal dimensions
        if width is None or height is None:
            calc_width, calc_height = calculate_destination_dimensions(ordered_points)
            width = width or calc_width
            height = height or calc_height
        
        # Ensure minimum dimensions
        width = max(width, 100)
        height = max(height, 100)
        
        # Use Apple's Accelerate framework via vImage
        try:
            import Foundation
            import Accelerate
            import Quartz
            from Cocoa import NSImage, NSData
            from Quartz.CoreGraphics import CGImage
            import io
            
            # Convert PIL image to RGBA if needed
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Save to temporary file for loading
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_file = tmp.name
                image.save(temp_file, format='PNG')
            
            try:
                # Create source image buffer
                source_url = Foundation.NSURL.fileURLWithPath_(temp_file)
                source_image = CGImage.imageWithContentsOfURL_(source_url)
                if source_image is None:
                    raise Exception("Failed to create CGImage from file")
                
                # Get image dimensions
                src_width = source_image.width()
                src_height = source_image.height()
                
                # Create vImage buffer from the CGImage
                src_format = Accelerate.vImage_CGImageFormat.createWithCGImage_(source_image)
                
                error = Foundation.NSInteger(0)
                src_buffer = Accelerate.vImage_Buffer()
                src_buffer = Accelerate.vImageBuffer_InitWithCGImage(
                    src_buffer,
                    src_format,
                    None,
                    Accelerate.kvImageNoFlags,
                    Foundation.byref(error))
                
                if error != 0:
                    raise Exception(f"Error creating source vImage buffer: {error}")
                
                # Create destination vImage buffer
                dest_buffer = Accelerate.vImage_Buffer()
                dest_buffer.width = Foundation.NSUInteger(width)
                dest_buffer.height = Foundation.NSUInteger(height)
                dest_buffer.rowBytes = Foundation.NSUInteger(4 * width)  # 4 bytes per pixel (RGBA)
                dest_buffer.data = Foundation.malloc_size(4 * width * height)
                
                # Create perspective transform
                # The points need to be in clockwise order: top-left, top-right, bottom-right, bottom-left
                src_coords = [
                    ordered_points[0]["x"], ordered_points[0]["y"],  # top-left
                    ordered_points[1]["x"], ordered_points[1]["y"],  # top-right
                    ordered_points[2]["x"], ordered_points[2]["y"],  # bottom-right
                    ordered_points[3]["x"], ordered_points[3]["y"]   # bottom-left
                ]
                
                # Destination coordinates are the corners of the output image
                dest_coords = [
                    0, 0,                # top-left
                    width, 0,            # top-right
                    width, height,       # bottom-right
                    0, height            # bottom-left
                ]
                
                # Create the 3x3 perspective transform matrix
                perspective_matrix = Accelerate.vImage_AffineTransform_CreatePerspectiveTransform(
                    Foundation.NSArray.arrayWithArray_(src_coords),
                    Foundation.NSArray.arrayWithArray_(dest_coords)
                )
                
                # Apply the perspective transform
                Accelerate.vImageWarpPerspective_ARGB8888(
                    src_buffer,
                    dest_buffer,
                    None,  # No background color (transparent)
                    perspective_matrix,
                    Accelerate.kvImageHighQualityResampling,
                    Foundation.byref(error)
                )
                
                if error != 0:
                    raise Exception(f"Error applying perspective transform: {error}")
                
                # Create CGImage from vImage buffer
                dest_image = Accelerate.vImageCreateCGImageFromBuffer(
                    dest_buffer,
                    src_format,
                    None,
                    None,
                    Accelerate.kvImageNoFlags,
                    Foundation.byref(error)
                )
                
                if error != 0 or dest_image is None:
                    raise Exception(f"Error creating CGImage from buffer: {error}")
                
                # Convert CGImage to NSImage
                ns_image = NSImage.alloc().initWithCGImage_size_(
                    dest_image, 
                    Foundation.NSMakeSize(width, height)
                )
                
                # Convert NSImage to PNG data
                tiff_data = ns_image.TIFFRepresentation()
                bitmap_rep = Quartz.NSBitmapImageRep.imageRepWithData_(tiff_data)
                png_data = bitmap_rep.representationUsingType_properties_(
                    Quartz.NSPNGFileType, None
                )
                
                # Create PIL Image from PNG data
                result_image = Image.open(io.BytesIO(png_data.bytes().tobytes()))
                
                # Clean up resources
                Foundation.free(dest_buffer.data)
                Accelerate.vImage_AffineTransform_Release(perspective_matrix)
                
                # Calculate metrics
                processing_time = time.time() - start_time
                metrics = calculate_metrics(result_image.width, result_image.height, processing_time)
                metrics["output_image"] = result_image
                metrics["method"] = "Apple Accelerate vImage"
                
                print(f"Apple Accelerate vImage transform successful in {processing_time:.2f} seconds")
                return metrics
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                
        except ImportError as e:
            print(f"Apple Accelerate libraries not available: {str(e)}")
            raise e
        except Exception as e:
            print(f"Error with Apple Accelerate method: {str(e)}")
            raise e
            
    except Exception as e:
        # Try to use Core Image as fallback
        try:
            import Foundation
            import Quartz
            from Cocoa import NSImage, CIImage, CIFilter, CIContext, CIVector
            import Quartz.CoreGraphics as CG
            import io
            
            print("Attempting Core Image transform as fallback")
            
            # Convert PIL image to RGBA if needed
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Save to temporary file for Core Image to load
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_file = tmp.name
                image.save(temp_file, format='PNG')
            
            try:
                # Create CIImage from the file URL
                image_url = Foundation.NSURL.fileURLWithPath_(temp_file)
                ci_image = CIImage.imageWithContentsOfURL_(image_url)
                if ci_image is None:
                    raise Exception("Failed to create CIImage from file")
                
                # Get original image dimensions
                original_width = image.width
                original_height = image.height
                
                # IMPORTANT: CIImage coordinates have origin at bottom-left, PIL has origin at top-left
                # Flip the y-coordinates
                source_points = [
                    CG.CGPoint(x=ordered_points[0]["x"], y=original_height - ordered_points[0]["y"]),  # top-left
                    CG.CGPoint(x=ordered_points[1]["x"], y=original_height - ordered_points[1]["y"]),  # top-right
                    CG.CGPoint(x=ordered_points[2]["x"], y=original_height - ordered_points[2]["y"]),  # bottom-right
                    CG.CGPoint(x=ordered_points[3]["x"], y=original_height - ordered_points[3]["y"])   # bottom-left
                ]
                
                # Create a perspective correction filter
                perspective_transform = CIFilter.filterWithName_("CIPerspectiveTransform")
                if perspective_transform is None:
                    raise Exception("Failed to create CIPerspectiveTransform filter")
                
                # Configure filter
                perspective_transform.setValue_forKey_(ci_image, "inputImage")
                perspective_transform.setValue_forKey_(CIVector.vectorWithCGPoint_(source_points[0]), "inputTopLeft")
                perspective_transform.setValue_forKey_(CIVector.vectorWithCGPoint_(source_points[1]), "inputTopRight")
                perspective_transform.setValue_forKey_(CIVector.vectorWithCGPoint_(source_points[3]), "inputBottomLeft")
                perspective_transform.setValue_forKey_(CIVector.vectorWithCGPoint_(source_points[2]), "inputBottomRight")
                
                # Get output image from filter
                output_ci_image = perspective_transform.valueForKey_("outputImage")
                if output_ci_image is None:
                    raise Exception("Failed to apply perspective transform filter")
                    
                # Create a context for rendering
                ci_context = CIContext.contextWithOptions_({"kCIContextUseSoftwareRenderer": False})
                
                # Create a CGRect for the desired output size
                output_rect = CG.CGRectMake(0, 0, width, height)
                
                # Create a CGImage from the CIImage, cropped to fit the desired dimensions
                output_cg_image = ci_context.createCGImage_fromRect_(output_ci_image, output_rect)
                
                if output_cg_image is None:
                    raise Exception("Failed to create CGImage from CIImage")
                
                # Convert CGImage to NSImage
                ns_image = NSImage.alloc().initWithCGImage_size_(output_cg_image, CG.CGSizeMake(width, height))
                
                # Convert NSImage to PNG data
                tiff_data = ns_image.TIFFRepresentation()
                bitmap_rep = Quartz.NSBitmapImageRep.imageRepWithData_(tiff_data)
                png_data = bitmap_rep.representationUsingType_properties_(Quartz.NSPNGFileType, None)
                
                # Convert back to PIL Image
                pil_image = Image.open(io.BytesIO(png_data.bytes().tobytes()))
                
                # Calculate metrics
                processing_time = time.time() - start_time
                
                metrics = calculate_metrics(pil_image.width, pil_image.height, processing_time)
                metrics["output_image"] = pil_image
                metrics["method"] = "Core Image"
                
                print(f"Core Image perspective transform successful in {processing_time:.2f} seconds")
                return metrics
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                
        except Exception as core_image_error:
            # If all else fails, try OpenCV
            try:
                import cv2
                
                print("Attempting OpenCV transform as third option")
                
                # Convert PIL image to OpenCV format
                img_cv = np.array(image)
                if image.mode == 'RGBA':
                    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGBA2BGRA)
                else:
                    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
                
                # Get source points array
                src_pts = np.array([
                    [ordered_points[0]["x"], ordered_points[0]["y"]],  # top-left
                    [ordered_points[1]["x"], ordered_points[1]["y"]],  # top-right
                    [ordered_points[2]["x"], ordered_points[2]["y"]],  # bottom-right
                    [ordered_points[3]["x"], ordered_points[3]["y"]]   # bottom-left
                ], dtype=np.float32)
                
                # Define destination points for a rectangle
                dst_pts = np.array([
                    [0, 0],               # top-left
                    [width-1, 0],         # top-right
                    [width-1, height-1],  # bottom-right
                    [0, height-1]         # bottom-left
                ], dtype=np.float32)
                
                # Calculate perspective transform matrix
                transform_matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
                
                # Apply perspective transformation with better interpolation
                warped = cv2.warpPerspective(
                    img_cv, 
                    transform_matrix, 
                    (width, height), 
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
                
                # Convert back to PIL Image
                if image.mode == 'RGBA':
                    warped = cv2.cvtColor(warped, cv2.COLOR_BGRA2RGBA)
                else:
                    warped = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
                
                result_image = Image.fromarray(warped)
                
                # Calculate metrics
                processing_time = time.time() - start_time
                metrics = calculate_metrics(width, height, processing_time)
                metrics["output_image"] = result_image
                metrics["method"] = "OpenCV"
                
                print(f"OpenCV perspective transform successful in {processing_time:.2f} seconds")
                return metrics
                
            except Exception as cv_error:
                # Last resort: use PIL
                try:
                    from PIL import ImageTransform
                    
                    print("Attempting PIL-based transform as last resort")
                    
                    # Create coefficient matrix for perspective transform
                    coeffs = ImageTransform.Perspective.getdata(
                        [(ordered_points[i]["x"], ordered_points[i]["y"]) for i in range(4)],
                        [(0, 0), (width-1, 0), (width-1, height-1), (0, height-1)]
                    )
                    
                    # Apply transform
                    result_image = image.transform(
                        (width, height),
                        Image.PERSPECTIVE,
                        coeffs,
                        Image.BICUBIC
                    )
                    
                    processing_time = time.time() - start_time
                    metrics = calculate_metrics(width, height, processing_time)
                    metrics["output_image"] = result_image
                    metrics["method"] = "PIL Transform"
                    
                    print(f"PIL Transform successful in {processing_time:.2f} seconds")
                    return metrics
                    
                except Exception as basic_error:
                    # If all transforms fail, return the original image with error
                    return handle_transform_error(e, image, start_time)


def visualize_perspective_points(image: Image.Image, points: List[Dict[str, float]]) -> Image.Image:
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
    
    # Draw calculated destination dimensions
    width, height = calculate_destination_dimensions(ordered_points)
    
    # Add informative text to the visualization
    font_color = (255, 255, 255)
    bg_color = (0, 0, 0, 160)
    
    # Draw a semi-transparent background for text
    draw.rectangle([(10, 10), (250, 100)], fill=bg_color)
    
    # Add legend explaining the colors
    draw.text((20, 20), "1:TL = Top Left (Red)", fill=(255, 0, 0))
    draw.text((20, 40), "2:TR = Top Right (Green)", fill=(0, 255, 0))
    draw.text((20, 60), "3:BR = Bottom Right (Blue)", fill=(0, 0, 255))
    draw.text((20, 80), "4:BL = Bottom Left (Yellow)", fill=(255, 255, 0))
    
    # Add more information about the calculated output dimensions
    text_y = 120
    draw.rectangle([(10, text_y), (350, text_y + 60)], fill=bg_color)
    
    draw.text((20, text_y), f"Original dimensions: {image.width}x{image.height}", fill=font_color)
    draw.text((20, text_y + 20), f"Calculated output: {width}x{height}", fill=font_color)
    
    # Calculate and show aspect ratio
    aspect_ratio = width / height if height > 0 else 0
    draw.text((20, text_y + 40), f"Aspect ratio: {aspect_ratio:.2f}", fill=font_color)
    
    return result


def detect_rectangle_macos(image: Image.Image) -> List[Dict[str, float]]:
    # Use image boundaries
    width, height = image.size
    points = [
        {"x": 0, "y": 0},
        {"x": width-1, "y": 0},
        {"x": width-1, "y": height-1},
        {"x": 0, "y": height-1}
    ]
    return points