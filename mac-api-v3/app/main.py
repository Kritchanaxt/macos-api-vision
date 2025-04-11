from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Query
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

# Import our modules
from app.ocr.engine import perform_ocr
from app.face.quality_detection import detect_face_quality
from app.card.detector import detect_card
from app.utils.image_processing import convert_to_supported_format
from app.utils.perspective import wrap_card_perspective
from app.models.schemas import OCRResponse, OCRRequest, FaceQualityResponse, CardDetectionResponse


# Create output folder if it doesn't exist
OUTPUT_FOLDER = "output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = FastAPI(
    title="Thai macOS Vision API",
    description="API for Thai OCR, face quality detection, and card detection using macOS Vision Framework",
    version="1.3.0"
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
    recognition_level: str = Form("accurate")
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
        processed_image.save(output_path)
        
        # Add output_path to result
        ocr_result["output_path"] = f"/output/{filename}"
        
        return OCRResponse(
            recognized_text=ocr_result["text"],
            confidence=ocr_result["confidence"],
            languages_detected=ocr_result["languages_detected"],
            dimensions=ocr_result["dimensions"],
            fast_rate=ocr_result["fast_rate"],
            rack_cooling_rate=ocr_result["rack_cooling_rate"],
            text_object_count=ocr_result["text_object_count"],
            processing_time=ocr_result["processing_time"],
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

@app.post("/card-perspective")
async def card_perspective_endpoint(
    file: UploadFile = File(...),
    card_id: int = Form(...),
    return_format: str = Form("base64"),  # "base64" or "json"
    save_debug_image: bool = Form(False)  # Option to save debug image with corner points
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
        
        # Find card by ID (supports both 0-indexed and 1-indexed)
        selected_card = None
        
        # Direct search first (for existing 1-indexed)
        for card in card_result["cards"]:
            if card["id"] == card_id:
                selected_card = card
                break
        
        # If not found, try adjusted ID (for 0-indexed case)
        if not selected_card and card_id >= 0 and card_id < len(card_result["cards"]):
            adjusted_id = card_id + 1
            for card in card_result["cards"]:
                if card["id"] == adjusted_id:
                    selected_card = card
                    break
        
        if not selected_card:
            raise HTTPException(status_code=404, detail=f"Card with ID {card_id} not found")
        
        # Adjust card perspective
        warped_card, metadata = wrap_card_perspective(processed_image, selected_card["corners"])
        
        if warped_card is None:
            raise HTTPException(status_code=500, detail="Could not adjust card perspective")
        
        # Save image to output folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"perspective_{timestamp}_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        warped_card.save(output_path)
        
        # Return data according to specified format
        if return_format == "base64":
            # Convert image to base64
            buffer = io.BytesIO()
            warped_card.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return JSONResponse({
                "format": "base64",
                "width": warped_card.width,
                "height": warped_card.height,
                "dimensions": metadata["dimensions"],
                "fast_rate": metadata["fast_rate"],
                "rack_cooling_rate": metadata["rack_cooling_rate"],
                "processing_time": metadata["processing_time"],
                "output_path": f"/output/{filename}"
            })
        else:
            # Return image directly
            return FileResponse(
                output_path,
                media_type="image/png",
                headers={
                    "X-Output-Path": f"/output/{filename}",
                    "X-Width": str(warped_card.width),
                    "X-Height": str(warped_card.height),
                    "X-Fast-Rate": str(metadata["fast_rate"]),
                    "X-Rack-Cooling-Rate": str(metadata["rack_cooling_rate"]),
                    "X-Processing-Time": str(metadata["processing_time"])
                }
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adjusting card perspective: {str(e)}")

    
# Add this section to run the app directly
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)