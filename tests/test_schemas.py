"""
Unit tests for Pydantic schemas in app/models/schemas.py
"""
import pytest
from app.models.schemas import (
    Point, TextElement, TextLine, ImageDimensions,
    OCRRequest, OCRResponse, FaceQualityResponse,
    CardDetectionResponse, PerspectiveTransformRequest, PerspectiveResponse
)


class TestPoint:
    """Test cases for Point schema"""
    
    def test_point_creation(self):
        """Test basic point creation"""
        point = Point(x=100.5, y=200.5)
        assert point.x == 100.5
        assert point.y == 200.5
    
    def test_point_with_integers(self):
        """Test point creation with integer values"""
        point = Point(x=100, y=200)
        assert point.x == 100
        assert point.y == 200
    
    def test_point_with_negative_values(self):
        """Test point creation with negative values"""
        point = Point(x=-50.5, y=-100.5)
        assert point.x == -50.5
        assert point.y == -100.5


class TestTextElement:
    """Test cases for TextElement schema"""
    
    def test_text_element_creation(self):
        """Test basic text element creation"""
        element = TextElement(
            id="elem_1",
            text="Hello World",
            confidence=0.95,
            position={"x": 10, "y": 20, "width": 100, "height": 30}
        )
        assert element.id == "elem_1"
        assert element.text == "Hello World"
        assert element.confidence == 0.95
        assert element.position == {"x": 10, "y": 20, "width": 100, "height": 30}
    
    def test_text_element_thai_text(self):
        """Test text element with Thai text"""
        element = TextElement(
            id="elem_thai",
            text="สวัสดีครับ",
            confidence=0.88,
            position={"x": 0, "y": 0, "width": 50, "height": 20}
        )
        assert element.text == "สวัสดีครับ"


class TestTextLine:
    """Test cases for TextLine schema"""
    
    def test_text_line_creation(self):
        """Test basic text line creation"""
        line = TextLine(
            id="line_1",
            text="This is a line of text",
            confidence=0.92,
            position={"x": 0, "y": 0, "width": 200, "height": 30}
        )
        assert line.id == "line_1"
        assert line.text == "This is a line of text"
        assert line.confidence == 0.92


class TestImageDimensions:
    """Test cases for ImageDimensions schema"""
    
    def test_image_dimensions_default_unit(self):
        """Test image dimensions with default unit"""
        dims = ImageDimensions(width=1920, height=1080)
        assert dims.width == 1920
        assert dims.height == 1080
        assert dims.unit == "pixel"
    
    def test_image_dimensions_custom_unit(self):
        """Test image dimensions with custom unit"""
        dims = ImageDimensions(width=100, height=200, unit="mm")
        assert dims.unit == "mm"


class TestOCRRequest:
    """Test cases for OCRRequest schema"""
    
    def test_ocr_request_defaults(self):
        """Test OCR request with default values"""
        request = OCRRequest()
        assert request.languages == "th-TH,en-US"
        assert request.recognition_level == "accurate"
        assert request.save_visualization == False
    
    def test_ocr_request_custom_values(self):
        """Test OCR request with custom values"""
        request = OCRRequest(
            languages="en-US,ja-JP",
            recognition_level="fast",
            save_visualization=True
        )
        assert request.languages == "en-US,ja-JP"
        assert request.recognition_level == "fast"
        assert request.save_visualization == True


class TestOCRResponse:
    """Test cases for OCRResponse schema"""
    
    def test_ocr_response_creation(self):
        """Test OCR response creation"""
        text_lines = {
            "line_1": TextLine(
                id="line_1",
                text="Test text",
                confidence=0.95,
                position={"x": 0, "y": 0, "width": 100, "height": 20}
            )
        }
        response = OCRResponse(
            document_type="card_id",
            recognized_text="Test text",
            confidence=0.95,
            text_lines=text_lines,
            dimensions=ImageDimensions(width=800, height=600),
            fast_rate=0.48,
            rack_cooling_rate=1.4,
            processing_time=0.123,
            text_object_count=1,
            output_path="/output/test.png"
        )
        assert response.document_type == "card_id"
        assert response.confidence == 0.95
        assert response.text_object_count == 1


class TestFaceQualityResponse:
    """Test cases for FaceQualityResponse schema"""
    
    def test_face_quality_response_no_face(self):
        """Test face quality response when no face detected"""
        response = FaceQualityResponse(
            has_face=False,
            face_count=0,
            processing_time=0.05,
            output_path="/output/face.png"
        )
        assert response.has_face == False
        assert response.face_count == 0
        assert response.quality_score is None
    
    def test_face_quality_response_with_face(self):
        """Test face quality response when face detected"""
        response = FaceQualityResponse(
            has_face=True,
            face_count=1,
            quality_score=0.85,
            position={"x": 100, "y": 100, "width": 200, "height": 200},
            dimensions=ImageDimensions(width=1920, height=1080),
            fast_rate=2.07,
            rack_cooling_rate=3.0,
            processing_time=0.15,
            output_path="/output/face.png"
        )
        assert response.has_face == True
        assert response.quality_score == 0.85


class TestCardDetectionResponse:
    """Test cases for CardDetectionResponse schema"""
    
    def test_card_detection_no_card(self):
        """Test card detection when no card found"""
        response = CardDetectionResponse(
            has_card=False,
            card_count=0,
            processing_time=0.1,
            output_path="/output/card.png"
        )
        assert response.has_card == False
        assert response.document_type == "id_card"
        assert response.confidence == 0.0
    
    def test_card_detection_with_card(self):
        """Test card detection when card found"""
        response = CardDetectionResponse(
            has_card=True,
            card_count=1,
            document_type="id_card",
            confidence=0.85,
            position={"x": 50, "y": 50, "width": 300, "height": 200},
            dimensions=ImageDimensions(width=640, height=480),
            fast_rate=0.31,
            rack_cooling_rate=1.12,
            processing_time=0.2,
            output_path="/output/card.png"
        )
        assert response.has_card == True
        assert response.confidence == 0.85


class TestPerspectiveTransformRequest:
    """Test cases for PerspectiveTransformRequest schema"""
    
    def test_perspective_request_basic(self):
        """Test perspective transform request with points"""
        points = [
            Point(x=0, y=0),
            Point(x=100, y=0),
            Point(x=100, y=100),
            Point(x=0, y=100)
        ]
        request = PerspectiveTransformRequest(points=points)
        assert len(request.points) == 4
        assert request.output_width is None
        assert request.output_height is None
    
    def test_perspective_request_with_dimensions(self):
        """Test perspective transform request with output dimensions"""
        points = [
            Point(x=0, y=0),
            Point(x=100, y=0),
            Point(x=100, y=100),
            Point(x=0, y=100)
        ]
        request = PerspectiveTransformRequest(
            points=points,
            output_width=800,
            output_height=600
        )
        assert request.output_width == 800
        assert request.output_height == 600


class TestPerspectiveResponse:
    """Test cases for PerspectiveResponse schema"""
    
    def test_perspective_response(self):
        """Test perspective response creation"""
        response = PerspectiveResponse(
            format="PNG",
            width=800,
            height=600,
            dimensions=ImageDimensions(width=800, height=600),
            fast_rate=0.48,
            rack_cooling_rate=1.4,
            processing_time=0.5,
            output_path="/output/perspective.png"
        )
        assert response.format == "PNG"
        assert response.width == 800
        assert response.height == 600
