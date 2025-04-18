from pydantic import BaseModel
from typing import List, Optional, Dict

class OCRRequest(BaseModel):
    """Model for OCR request"""
    languages: List[str] = ["th-TH", "en-US"]  # Default: Thai and English
    recognition_level: str = "accurate"  # Default: accurate

class ImageDimensions(BaseModel):
    """Model for image dimensions"""
    width: int
    height: int

class OCRResponse(BaseModel):
    """Model for OCR response"""
    recognized_text: str
    confidence: float
    languages_detected: List[str]
    dimensions: ImageDimensions
    fast_rate: float
    rack_cooling_rate: float
    text_object_count: int
    processing_time: float  # Processing time (seconds)
    output_path: Optional[str] = None  # Path to output file

class FaceQualityPoint(BaseModel):
    """Model for point coordinates"""
    x: float
    y: float

class FaceBoundingBox(BaseModel):
    """Model for face bounding box"""
    x: float
    y: float
    width: float
    height: float

class FaceInfo(BaseModel):
    """Model for face information"""
    bbox: FaceBoundingBox
    quality_score: float
    has_landmarks: bool

class FaceQualityResponse(BaseModel):
    """Model for face quality response"""
    face_count: int
    faces: List[FaceInfo]
    average_quality: float
    dimensions: ImageDimensions
    fast_rate: float
    rack_cooling_rate: float
    processing_time: float
    error: Optional[str] = None
    output_path: Optional[str] = None  # Path to output file

class CardCorner(BaseModel):
    """Model for card corner"""
    x: float
    y: float

class CardBoundingBox(BaseModel):
    """Model for card bounding box"""
    x: float
    y: float
    width: float
    height: float

class CardInfo(BaseModel):
    """Model for card information"""
    id: int
    corners: List[CardCorner]
    confidence: float
    bbox: CardBoundingBox

class CardDetectionResponse(BaseModel):
    """Model for card detection response"""
    card_count: int
    cards: List[CardInfo]
    dimensions: ImageDimensions
    fast_rate: float
    rack_cooling_rate: float
    processing_time: float
    error: Optional[str] = None
    output_path: Optional[str] = None  # Path to output file

# New models for perspective transformation
class Point(BaseModel):
    """Model for a 2D point"""
    x: float
    y: float

class PerspectiveTransformRequest(BaseModel):
    """Model for perspective transformation request"""
    points: List[Point]
    width: Optional[int] = None
    height: Optional[int] = None

class PerspectiveResponse(BaseModel):
    """Model for perspective transformation response"""
    format: str
    width: int
    height: int
    dimensions: ImageDimensions
    fast_rate: float
    rack_cooling_rate: float
    processing_time: float
    output_path: str