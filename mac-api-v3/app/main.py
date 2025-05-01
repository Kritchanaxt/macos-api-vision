from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Query, Body
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import io
from PIL import Image
import uvicorn
import sys
import os
import base64
from datetime import datetime
import uuid
import json
from typing import Dict, List, Optional, Union, Tuple


try:
    # Try importing from app structure first
    from app.ocr.engine import perform_ocr
    from app.face.quality_detection import detect_face_quality
    from app.card.detector import detect_card
    from app.utils.image_processing import convert_to_supported_format
    from app.wrap.correct_perspective import correct_perspective
    from app.wrap.detect_rectangle import detect_document_edges
    from app.wrap.enhance_image import enhance_image  # Import enhance_image

except ImportError:
    # If that fails, try importing from the current directory
    try:
        # If the files are in the same directory as main.py
        from ocr.engine import perform_ocr
        from face.quality_detection import detect_face_quality
        from card.detector import detect_card
        from utils.image_processing import convert_to_supported_format
        from wrap.correct_perspective import correct_perspective
        from wrap.detect_rectangle import detect_document_edges
        from wrap.enhance_image import enhance_image  # Import enhance_image

    except ImportError:
        # If that also fails, raise an informative error
        raise ImportError("Could not import required modules. Please check file structure.")

# Adjust schema imports if needed
try:
    from app.models.schemas import (
        OCRResponse, OCRRequest, FaceQualityResponse, CardDetectionResponse,
        PerspectiveTransformRequest, PerspectiveResponse, Point, Optional, List,
        TextLine, TextElement, ImageDimensions
    )
except ImportError:
    try:
        from schemas import (
            OCRResponse, OCRRequest, FaceQualityResponse, CardDetectionResponse,
            PerspectiveTransformRequest, PerspectiveResponse, Point, Optional, List,
            TextLine, TextElement, ImageDimensions, 
        )
    except ImportError:
        raise ImportError("Could not import schema models. Please check file structure.")


# Create output folder if it doesn't exist
OUTPUT_FOLDER = "output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Create static folder if it doesn't exist
STATIC_FOLDER = "static"
os.makedirs(STATIC_FOLDER, exist_ok=True)

app = FastAPI(
    title="Thai macOS Vision API",
    description="API for Thai OCR, face quality detection, card detection, and perspective transformation using macOS Vision Framework",
    version="1.7.0"  # Updated version to reflect the addition of perspective correction UI
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory=STATIC_FOLDER), name="static")

# Helper functions for image processing
def get_image_dimensions(image):
    """Get image dimensions"""
    width, height = image.size
    return {"width": width, "height": height, "unit": "pixel"}

def calculate_fast_rate(width, height):
    """Calculate fast rate based on image dimensions"""
    return (width * height) / 1000000.0  # Example metric

def calculate_rack_cooling_rate(width, height):
    """Calculate rack cooling rate based on image dimensions"""
    return (width + height) / 1000.0  # Example metric

@app.get("/")
async def root():
    """Root endpoint to check if API is running"""
    return FileResponse(os.path.join(STATIC_FOLDER, "index.html"))

@app.get("/output/{filename}")
async def get_output_file(filename: str):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

@app.post("/ocr", response_model=OCRResponse)
async def ocr_endpoint(
    file: UploadFile = File(...),
    languages: str = Form("th-TH,en-US"),  # Default: Thai and English
    recognition_level: str = Form("accurate"),
    save_visualization: bool = Form(False)  # Option to save visualization with bounding boxes
):
    # Check operating system
    if sys.platform != "darwin":
        raise HTTPException(status_code=400, detail="This API works only on macOS")
    
    try:
        # Read image file
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert image to supported format
        processed_image = convert_to_supported_format(image)
        
        # Split languages into list
        language_list = [lang.strip() for lang in languages.split(",")]
        
        # Process OCR
        ocr_result = perform_ocr(processed_image, language_list, recognition_level)

        # Save image to output folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ocr_{timestamp}_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        
        # Save visualization if requested
        if save_visualization and "visualization_image" in ocr_result:
            ocr_result["visualization_image"].save(output_path)
        else:
            processed_image.save(output_path)
        
        # Add output_path to result
        ocr_result["output_path"] = f"/output/{filename}"
        
        # Remove visualization_image from result before returning (not needed in response)
        if "visualization_image" in ocr_result:
            del ocr_result["visualization_image"]
        
        # Create dimensions object
        dimensions = ImageDimensions(
            width=ocr_result["dimensions"]["width"],
            height=ocr_result["dimensions"]["height"],
            unit=ocr_result["dimensions"]["unit"]
        )
        
        # Convert text_lines dict to TextLine objects
        text_lines = {}
        for key, line in ocr_result["text_lines"].items():
            text_lines[key] = TextLine(
                id=line["id"],
                text=line["text"],
                confidence=line["confidence"],
                position=line["position"]
            )
        
        return OCRResponse(
            document_type=ocr_result["document_type"],
            recognized_text=ocr_result["recognized_text"],
            confidence=ocr_result["confidence"],
            text_lines=text_lines,
            dimensions=dimensions,
            fast_rate=ocr_result["fast_rate"],
            rack_cooling_rate=ocr_result["rack_cooling_rate"],
            processing_time=ocr_result["processing_time"],
            text_object_count=ocr_result["text_object_count"],
            output_path=ocr_result["output_path"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing OCR: {str(e)}")

@app.post("/ocr/base64", response_model=OCRResponse)
async def ocr_base64_endpoint(
    image_base64: str = Body(..., embed=True),
    languages: str = Body("th-TH,en-US"),  # Default: Thai and English
    recognition_level: str = Body("accurate"),
    save_visualization: bool = Body(False)  # Option to save visualization with bounding boxes
):
    # Check operating system
    if sys.platform != "darwin":
        raise HTTPException(status_code=400, detail="This API works only on macOS")
    
    try:
        # Decode base64 image
        try:
            # Remove data URI prefix if present
            if "base64," in image_base64:
                image_base64 = image_base64.split("base64,")[1]
                
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image: {str(e)}")
        
        # Convert image to supported format
        processed_image = convert_to_supported_format(image)
        
        # Split languages into list
        language_list = [lang.strip() for lang in languages.split(",")]
        
        # Process OCR
        ocr_result = perform_ocr(processed_image, language_list, recognition_level)

        # Save image to output folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ocr_{timestamp}_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        
        # Save visualization if requested
        if save_visualization and "visualization_image" in ocr_result:
            ocr_result["visualization_image"].save(output_path)
        else:
            processed_image.save(output_path)
        
        # Add output_path to result
        ocr_result["output_path"] = f"/output/{filename}"
        
        # Remove visualization_image from result before returning (not needed in response)
        if "visualization_image" in ocr_result:
            del ocr_result["visualization_image"]
        
        # Create dimensions object
        dimensions = ImageDimensions(
            width=ocr_result["dimensions"]["width"],
            height=ocr_result["dimensions"]["height"],
            unit=ocr_result["dimensions"]["unit"]
        )
        
        # Convert text_lines dict to TextLine objects
        text_lines = {}
        for key, line in ocr_result["text_lines"].items():
            text_lines[key] = TextLine(
                id=line["id"],
                text=line["text"],
                confidence=line["confidence"],
                position=line["position"]
            )
        
        return OCRResponse(
            document_type=ocr_result["document_type"],
            recognized_text=ocr_result["recognized_text"],
            confidence=ocr_result["confidence"],
            text_lines=text_lines,
            dimensions=dimensions,
            fast_rate=ocr_result["fast_rate"],
            rack_cooling_rate=ocr_result["rack_cooling_rate"],
            processing_time=ocr_result["processing_time"],
            text_object_count=ocr_result["text_object_count"],
            output_path=ocr_result["output_path"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing OCR: {str(e)}")


@app.post("/face-quality", response_model=FaceQualityResponse)
async def face_quality_endpoint(
    file: UploadFile = File(...),
    save_visualization: bool = Form(True)  # Option to save visualization with bounding boxes
):
    # Check operating system
    if sys.platform != "darwin":
        raise HTTPException(status_code=400, detail="This API works only on macOS")
    
    try:
        # Read image file
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert image to supported format
        processed_image = convert_to_supported_format(image)
        
        # Check face quality
        face_result = detect_face_quality(processed_image)
        
        # Save image to output folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"face_{timestamp}_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        
        # Save visualization if requested
        if save_visualization and "output_image" in face_result:
            face_result["output_image"].save(output_path)
        else:
            processed_image.save(output_path)
        
        # Add output_path to result
        face_result["output_path"] = f"/output/{filename}"
        
        # Remove output_image from result before returning (not needed in response)
        if "output_image" in face_result:
            del face_result["output_image"]
        
        return face_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking face quality: {str(e)}")


@app.post("/card-detect", response_model=CardDetectionResponse)
async def card_detection_endpoint(
    file: UploadFile = File(...),
    save_visualization: bool = Form(True)  # Option to save visualization with bounding boxes
):
    # Check operating system
    if sys.platform != "darwin":
        raise HTTPException(status_code=400, detail="This API works only on macOS")
    
    try:
        # Read image file
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert image to supported format
        processed_image = convert_to_supported_format(image)
        
        # Detect cards
        card_result = detect_card(processed_image)
        
        # Save image to output folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"card_{timestamp}_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        
        # Save visualization if requested
        if save_visualization and "output_image" in card_result:
            card_result["output_image"].save(output_path)
        else:
            processed_image.save(output_path)
        
        # Add output_path to result
        card_result["output_path"] = f"/output/{filename}"
        
        # Remove output_image from result before returning (not needed in response)
        if "output_image" in card_result:
            del card_result["output_image"]
        
        return card_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting card: {str(e)}")

@app.post("/perspective", response_model=PerspectiveResponse)
async def perspective_endpoint(
    file: UploadFile = File(...),
    points: str = Form(...),  # Format: [{"x":100,"y":100},{"x":300,"y":100},{"x":300,"y":300},{"x":100,"y":300}]
    output_width: Optional[int] = Form(None),
    output_height: Optional[int] = Form(None)
):
    # Check operating system
    if sys.platform != "darwin":
        raise HTTPException(status_code=400, detail="This API works only on macOS")
    
    try:
        # Read image file
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert image to supported format
        processed_image = convert_to_supported_format(image)
        
        # Parse points from JSON string
        try:
            points_data = json.loads(points)
            if len(points_data) != 4:
                raise HTTPException(status_code=400, detail="Exactly 4 points must be provided")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for points")
        
        # Convert PIL Image to CoreImage for perspective correction
        import io
        from Foundation import NSData
        from Cocoa import CIImage
        from Foundation import NSPoint
        
        # Convert PIL Image to CIImage
        buffer = io.BytesIO()
        processed_image.save(buffer, format="PNG")
        ns_data = NSData.dataWithBytes_length_(buffer.getvalue(), len(buffer.getvalue()))
        ci_image = CIImage.imageWithData_(ns_data)
        
        # Create NSPoint objects from the provided points
        # Points are expected in order: top-left, top-right, bottom-right, bottom-left
        top_left = NSPoint(points_data[0]["x"], points_data[0]["y"])
        top_right = NSPoint(points_data[1]["x"], points_data[1]["y"])
        bottom_right = NSPoint(points_data[2]["x"], points_data[2]["y"])
        bottom_left = NSPoint(points_data[3]["x"], points_data[3]["y"])
        
        # Apply perspective correction
        corrected_ci_image = correct_perspective(ci_image, top_left, top_right, bottom_right, bottom_left)
        
        # Apply image enhancement (Sharpen filter)
        enhanced_ci_image = enhance_image(corrected_ci_image)
        
        # Convert CIImage back to PIL Image
        from Quartz import CIContext
        import numpy as np
        
        context = CIContext.contextWithOptions_(None)
        cgimage = context.createCGImage_fromRect_(enhanced_ci_image, enhanced_ci_image.extent())
        
        # Get dimensions
        width = int(enhanced_ci_image.extent().size.width)
        height = int(enhanced_ci_image.extent().size.height)
        
        # Create a buffer for the image data
        from Quartz import CGColorSpaceCreateDeviceRGB, CGBitmapContextCreate, CGRectMake
        from Quartz import CGContextDrawImage, CGBitmapContextCreateImage
        
        colorspace = CGColorSpaceCreateDeviceRGB()
        context = CGBitmapContextCreate(
            None, width, height, 8, 4 * width, colorspace,
            0x2  # kCGImageAlphaPremultipliedFirst | kCGBitmapByteOrder32Little
        )
        
        CGContextDrawImage(context, CGRectMake(0, 0, width, height), cgimage)
        cgimage = CGBitmapContextCreateImage(context)
        
        # Get image data from CGImageRef
        from CoreGraphics import CGDataProviderCopyData, CGImageGetDataProvider
        data_provider = CGImageGetDataProvider(cgimage)
        data = CGDataProviderCopyData(data_provider)
        buffer = np.frombuffer(data, dtype=np.uint8)
        
        # Reshape and convert to PIL Image
        buffer = buffer.reshape((height, width, 4))
        result_image = Image.fromarray(buffer, mode="RGBA")
        
        # Resize image if output dimensions are specified (using Pillow as requested)
        if output_width and output_height:
            result_image = result_image.resize((output_width, output_height), Image.LANCZOS)
        
        # Save image to output folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"perspective_{timestamp}_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        result_image.save(output_path)
        
        # Calculate metrics
        img_dimensions = get_image_dimensions(result_image)
        fast_rate = calculate_fast_rate(img_dimensions["width"], img_dimensions["height"])
        rack_cooling_rate = calculate_rack_cooling_rate(img_dimensions["width"], img_dimensions["height"])
        
        # Create response
        response = PerspectiveResponse(
            format="png",
            width=img_dimensions["width"],
            height=img_dimensions["height"],
            dimensions=ImageDimensions(
                width=img_dimensions["width"],
                height=img_dimensions["height"],
                unit="pixel"
            ),
            fast_rate=fast_rate,
            rack_cooling_rate=rack_cooling_rate,
            processing_time=0.0,  # Can add actual processing time if needed
            output_path=f"/output/{filename}"
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in perspective correction: {str(e)}")

@app.post("/perspective/detect-rectangle", response_model=Dict[str, List[Dict[str, float]]])
async def detect_rectangle_endpoint(
    file: UploadFile = File(...)
):
    # Check operating system
    if sys.platform != "darwin":
        raise HTTPException(status_code=400, detail="This API works only on macOS")
    
    try:
        # Read image file
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert image to supported format
        processed_image = convert_to_supported_format(image)
        
        # Convert PIL Image to CoreImage
        import io
        from Foundation import NSData
        from Cocoa import CIImage
        
        # Convert PIL Image to CIImage
        buffer = io.BytesIO()
        processed_image.save(buffer, format="PNG")
        ns_data = NSData.dataWithBytes_length_(buffer.getvalue(), len(buffer.getvalue()))
        ci_image = CIImage.imageWithData_(ns_data)
        
        # Detect document edges
        try:
            top_left, top_right, bottom_right, bottom_left = detect_document_edges(ci_image)
            
            # Convert NSPoint objects to dictionaries
            points = [
                {"x": top_left.x, "y": top_left.y},
                {"x": top_right.x, "y": top_right.y},
                {"x": bottom_right.x, "y": bottom_right.y},
                {"x": bottom_left.x, "y": bottom_left.y}
            ]
            
            return {"points": points}
            
        except ValueError as ve:
            # If no document edges detected, return default points
            width, height = processed_image.size
            points = [
                {"x": 0.05 * width, "y": 0.05 * height},
                {"x": 0.95 * width, "y": 0.05 * height},
                {"x": 0.95 * width, "y": 0.95 * height},
                {"x": 0.05 * width, "y": 0.95 * height}
            ]
            return {"points": points}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting rectangle: {str(e)}")

# Add this at the end of the file
if __name__ == "__main__":
    # Start the FastAPI application
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)