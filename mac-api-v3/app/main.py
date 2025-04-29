from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Query, Body
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import io
from PIL import Image
import uvicorn
import sys
import os
import base64
from datetime import datetime
import uuid
import json

try:
    # Try importing from app structure first
    from app.ocr.engine import perform_ocr
    from app.face.quality_detection import detect_face_quality
    from app.card.detector import detect_card
    from app.utils.image_processing import convert_to_supported_format
    from app.utils.perspective_transform import perform_perspective_transform_macos as perform_perspective_transform
    from app.utils.perspective_transform import visualize_perspective_points
except ImportError:
    # If that fails, try importing from the current directory
    try:
        # If the files are in the same directory as main.py
        from ocr.engine import perform_ocr
        from face.quality_detection import detect_face_quality
        from card.detector import detect_card
        from utils.image_processing import convert_to_supported_format
        from utils.perspective_transform import perform_perspective_transform_macos as perform_perspective_transform
        from utils.perspective_transform import visualize_perspective_points
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
            TextLine, TextElement, ImageDimensions
        )
    except ImportError:
        raise ImportError("Could not import schema models. Please check file structure.")


# Create output folder if it doesn't exist
OUTPUT_FOLDER = "output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = FastAPI(
    title="Thai macOS Vision API",
    description="API for Thai OCR, face quality detection, card detection, and perspective transformation using macOS Vision Framework",
    version="1.6.0"  # Updated version to reflect the refactoring
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint to check if API is running"""
    return {"message": "Thai macOS Vision API is ready"}

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
    points: str = Form(...),  # JSON string with points [{"x": x1, "y": y1}, ...]
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    visualize_only: bool = Form(False)  # If true, just return visualization without transformation
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
            points_list = json.loads(points)
            
            # Validate points
            if len(points_list) != 4:
                raise HTTPException(status_code=400, detail="Exactly 4 points are required for perspective transformation")
            
            # Validate each point has x and y
            for point in points_list:
                if "x" not in point or "y" not in point:
                    raise HTTPException(status_code=400, detail="Each point must have 'x' and 'y' coordinates")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for points")
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        
        # If visualize_only is True, just return a visualization of the points
        if visualize_only:
            visual_image = visualize_perspective_points(processed_image, points_list)
            
            # Save visualization
            filename = f"perspective_viz_{timestamp}_{unique_id}.png"
            output_path = os.path.join(OUTPUT_FOLDER, filename)
            visual_image.save(output_path)
            
            # Get dimensions
            dimensions = {
                "width": visual_image.width,
                "height": visual_image.height
            }
            
            # Calculate rates
            fast_rate = (dimensions["width"] * dimensions["height"]) / 1000000
            rack_cooling_rate = (dimensions["width"] + dimensions["height"]) / 1000
            
            return PerspectiveResponse(
                format="PNG",
                width=dimensions["width"],
                height=dimensions["height"],
                dimensions=dimensions,
                fast_rate=fast_rate,
                rack_cooling_rate=rack_cooling_rate,
                processing_time=0.0,  # Just visualization, no transformation processing
                output_path=f"/output/{filename}"
            )
        
        # Perform perspective transformation
        result = perform_perspective_transform(
            processed_image,
            points_list,
            width=width,
            height=height
        )
        
        # Save transformed image
        filename = f"perspective_{timestamp}_{unique_id}.png"
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        result["output_image"].save(output_path)
        
        # Add output_path to result
        result["output_path"] = f"/output/{filename}"
        
        # Remove output_image from result before returning
        del result["output_image"]
        
        return PerspectiveResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing perspective transformation: {str(e)}")


# Add this endpoint to allow input of base64 image instead of file upload
@app.post("/perspective/base64", response_model=PerspectiveResponse)
async def perspective_base64_endpoint(
    image_base64: str = Body(..., embed=True),
    points: List[Point] = Body(...),
    width: Optional[int] = Body(None),
    height: Optional[int] = Body(None),
    visualize_only: bool = Body(False)
):
    # Check operating system
    if sys.platform != "darwin":
        raise HTTPException(status_code=400, detail="This API works only on macOS")
    
    try:
        # Decode base64 image
        try:
            # Remove data URI prefix if present (e.g., "data:image/jpeg;base64,")
            if "base64," in image_base64:
                image_base64 = image_base64.split("base64,")[1]
                
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image: {str(e)}")
        
        # Convert image to supported format
        processed_image = convert_to_supported_format(image)
        
        # Convert Pydantic Points to dict format
        points_list = [{"x": point.x, "y": point.y} for point in points]
        
        # Validate points
        if len(points_list) != 4:
            raise HTTPException(status_code=400, detail="Exactly 4 points are required for perspective transformation")
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        
        # If visualize_only is True, just return a visualization of the points
        if visualize_only:
            visual_image = visualize_perspective_points(processed_image, points_list)
            
            # Save visualization
            filename = f"perspective_viz_{timestamp}_{unique_id}.png"
            output_path = os.path.join(OUTPUT_FOLDER, filename)
            visual_image.save(output_path)
            
            # Get dimensions
            dimensions = {
                "width": visual_image.width,
                "height": visual_image.height
            }
            
            # Calculate rates
            fast_rate = (dimensions["width"] * dimensions["height"]) / 1000000
            rack_cooling_rate = (dimensions["width"] + dimensions["height"]) / 1000
            
            return PerspectiveResponse(
                format="PNG",
                width=dimensions["width"],
                height=dimensions["height"],
                dimensions=dimensions,
                fast_rate=fast_rate,
                rack_cooling_rate=rack_cooling_rate,
                processing_time=0.0,
                output_path=f"/output/{filename}"
            )
        
        # Perform perspective transformation
        result = perform_perspective_transform(
            processed_image,
            points_list,
            width=width,
            height=height
        )
        
        # Save transformed image
        filename = f"perspective_{timestamp}_{unique_id}.png"
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        result["output_image"].save(output_path)
        
        # Add output_path to result
        result["output_path"] = f"/output/{filename}"
        
        # Remove output_image from result before returning
        del result["output_image"]
        
        return PerspectiveResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing perspective transformation: {str(e)}")

    
# Add this section to run the app directly
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)