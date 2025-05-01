from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class Point(BaseModel):
    x: float
    y: float

class TextElement(BaseModel):
    id: str
    text: str
    confidence: float
    position: Dict[str, float]

class TextLine(BaseModel):
    id: str
    text: str
    confidence: float
    position: Dict[str, float]

class ImageDimensions(BaseModel):
    width: int
    height: int
    unit: str = "pixel"

class OCRRequest(BaseModel):
    languages: str = "th-TH,en-US"
    recognition_level: str = "accurate"
    save_visualization: bool = False

class OCRResponse(BaseModel):
    document_type: str
    recognized_text: str
    confidence: float
    text_lines: Dict[str, TextLine]
    dimensions: ImageDimensions
    fast_rate: float
    rack_cooling_rate: float
    processing_time: float
    text_object_count: int
    output_path: str

class FaceQualityResponse(BaseModel):
    has_face: bool
    face_count: int = 0
    quality_score: Optional[float] = None
    position: Optional[Dict[str, Any]] = None
    dimensions: Optional[ImageDimensions] = None
    fast_rate: Optional[float] = None
    rack_cooling_rate: Optional[float] = None
    processing_time: float
    output_path: str

class CardDetectionResponse(BaseModel):
    has_card: bool
    card_count: int = 0
    card_type: Optional[str] = None
    position: Optional[Dict[str, Any]] = None
    dimensions: Optional[ImageDimensions] = None
    fast_rate: Optional[float] = None
    rack_cooling_rate: Optional[float] = None
    processing_time: float
    output_path: str

class PerspectiveTransformRequest(BaseModel):
    points: List[Point]
    output_width: Optional[int] = None
    output_height: Optional[int] = None

class PerspectiveResponse(BaseModel):
    format: str
    width: int
    height: int
    dimensions: ImageDimensions
    fast_rate: float
    rack_cooling_rate: float
    processing_time: float
    output_path: str