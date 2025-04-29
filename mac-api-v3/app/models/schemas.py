from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Literal


class OCRRequest(BaseModel):
    """Model for OCR request"""
    languages: List[str] = ["th-TH", "en-US"]  # Default: Thai and English
    recognition_level: str = "accurate"  # Default: accurate


class ImageDimensions(BaseModel):
    """Model for image dimensions"""
    width: int
    height: int
    unit: Literal["pixel"] = "pixel"


class TextPosition(BaseModel):
    """Model for text position"""
    x: float
    y: float
    width: float
    height: float
    unit: Literal["pixel"] = "pixel"
    

class TextElement(BaseModel):
    """Model for individual text element"""
    id: str
    text: str
    confidence: float
    position: TextPosition


class TextLine(BaseModel):
    """Model for text line"""
    id: str
    text: str
    confidence: float
    position: TextPosition


class OCRResponse(BaseModel):
    """Model for OCR response"""
    document_type: str = "unknown"  # Type of document (e.g., "card_id", "passport", etc.)
    recognized_text: str
    confidence: float
    text_lines: Dict[str, TextLine]  # Organized text by lines with clear IDs
    dimensions: ImageDimensions
    fast_rate: float
    rack_cooling_rate: float
    processing_time: float  # Processing time (seconds)
    text_object_count: int
    output_path: Optional[str] = None  # Path to output file


class FaceQualityPoint(BaseModel):
    """Model for point coordinates"""
    x: float
    y: float
    unit: Literal["pixel"] = "pixel"


class FaceBoundingBox(BaseModel):
    """Model for face bounding box"""
    x: float
    y: float
    width: float
    height: float
    unit: Literal["pixel"] = "pixel"


class FaceInfo(BaseModel):
    """Model for face information"""
    id: str
    bbox: FaceBoundingBox
    quality_score: float
    has_landmarks: bool


class FaceQualityResponse(BaseModel):
    """Model for face quality response"""
    faces: List[FaceInfo]
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
    unit: Literal["pixel"] = "pixel"


class CardBoundingBox(BaseModel):
    """Model for card bounding box"""
    x: float
    y: float
    width: float
    height: float
    unit: Literal["pixel"] = "pixel"


class CardInfo(BaseModel):
    """Model for card information"""
    id: str
    corners: List[CardCorner]
    confidence: float
    bbox: CardBoundingBox


class CardDetectionResponse(BaseModel):
    """Model for card detection response"""
    cards: List[CardInfo]
    dimensions: ImageDimensions
    fast_rate: float
    rack_cooling_rate: float
    processing_time: float
    error: Optional[str] = None
    output_path: Optional[str] = None  # Path to output file


# Models for perspective transformation
class Point(BaseModel):
    """Model for a 2D point"""
    x: float
    y: float
    unit: Literal["pixel"] = "pixel"


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