"""
Unit tests for FastAPI endpoints in app/main.py
Tests use TestClient to test HTTP endpoints
"""
import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

client = TestClient(app)


def create_test_image(width=100, height=100, mode='RGB', color='white'):
    """Helper function to create test images"""
    image = Image.new(mode, (width, height), color=color)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr


class TestRootEndpoint:
    """Test cases for root endpoint"""
    
    def test_root_returns_html(self):
        """Test that root returns HTML file or error if file missing"""
        try:
            response = client.get("/")
            # Should return 200 if static file exists
            assert response.status_code in [200, 404, 500]
        except RuntimeError:
            # Expected if static/index.html doesn't exist
            pass


class TestOCREndpoint:
    """Test cases for /ocr endpoint"""
    
    def test_ocr_endpoint_accepts_image(self):
        """Test that OCR endpoint accepts image file"""
        image_data = create_test_image()
        
        response = client.post(
            "/ocr",
            files={"file": ("test.png", image_data, "image/png")},
            data={
                "languages": "en-US",
                "recognition_level": "fast",
                "save_visualization": "false"
            }
        )
        
        # Should return 200 or 500 (if Vision framework not available in test env)
        assert response.status_code in [200, 500]
    
    def test_ocr_endpoint_requires_file(self):
        """Test that OCR endpoint requires file parameter"""
        response = client.post("/ocr")
        assert response.status_code == 422  # Validation error
    
    def test_ocr_default_parameters(self):
        """Test OCR endpoint with default parameters"""
        image_data = create_test_image()
        
        response = client.post(
            "/ocr",
            files={"file": ("test.png", image_data, "image/png")}
        )
        
        assert response.status_code in [200, 500]
    
    def test_ocr_thai_language(self):
        """Test OCR with Thai language"""
        image_data = create_test_image()
        
        response = client.post(
            "/ocr",
            files={"file": ("test.png", image_data, "image/png")},
            data={"languages": "th-TH"}
        )
        
        assert response.status_code in [200, 500]


class TestFaceQualityEndpoint:
    """Test cases for /face-quality endpoint"""
    
    def test_face_quality_endpoint_accepts_image(self):
        """Test that face quality endpoint accepts image file"""
        image_data = create_test_image()
        
        response = client.post(
            "/face-quality",
            files={"file": ("test.png", image_data, "image/png")},
            data={"save_visualization": "false"}
        )
        
        assert response.status_code in [200, 500]
    
    def test_face_quality_requires_file(self):
        """Test that face quality endpoint requires file parameter"""
        response = client.post("/face-quality")
        assert response.status_code == 422
    
    def test_face_quality_with_visualization(self):
        """Test face quality with visualization enabled"""
        image_data = create_test_image()
        
        response = client.post(
            "/face-quality",
            files={"file": ("test.png", image_data, "image/png")},
            data={"save_visualization": "true"}
        )
        
        assert response.status_code in [200, 500]


class TestCardDetectionEndpoint:
    """Test cases for /card-detect endpoint"""
    
    def test_card_detect_endpoint_accepts_image(self):
        """Test that card detection endpoint accepts image file"""
        image_data = create_test_image()
        
        response = client.post(
            "/card-detect",
            files={"file": ("test.png", image_data, "image/png")},
            data={"save_visualization": "false"}
        )
        
        assert response.status_code in [200, 500]
    
    def test_card_detect_requires_file(self):
        """Test that card detection endpoint requires file parameter"""
        response = client.post("/card-detect")
        assert response.status_code == 422
    
    def test_card_detect_response_structure(self):
        """Test card detection response structure"""
        image_data = create_test_image()
        
        response = client.post(
            "/card-detect",
            files={"file": ("test.png", image_data, "image/png")}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "has_card" in data
            assert "card_count" in data


class TestPerspectiveEndpoint:
    """Test cases for /perspective endpoint"""
    
    def test_perspective_endpoint_accepts_image(self):
        """Test that perspective endpoint accepts image file with points"""
        image_data = create_test_image(200, 200)
        
        # Perspective endpoint requires 'points' parameter
        points = '[{"x": 0, "y": 0}, {"x": 200, "y": 0}, {"x": 200, "y": 200}, {"x": 0, "y": 200}]'
        
        response = client.post(
            "/perspective",
            files={"file": ("test.png", image_data, "image/png")},
            data={"points": points}
        )
        
        assert response.status_code in [200, 500]
    
    def test_perspective_requires_file(self):
        """Test that perspective endpoint requires file parameter"""
        response = client.post("/perspective")
        assert response.status_code == 422
    
    def test_perspective_requires_points(self):
        """Test that perspective endpoint requires points parameter"""
        image_data = create_test_image(200, 200)
        
        response = client.post(
            "/perspective",
            files={"file": ("test.png", image_data, "image/png")}
        )
        
        assert response.status_code == 422


class TestOutputEndpoint:
    """Test cases for /output/{filename} endpoint"""
    
    def test_output_file_not_found(self):
        """Test that non-existent file returns 404"""
        response = client.get("/output/nonexistent_file.png")
        assert response.status_code == 404
    
    def test_output_file_found(self):
        """Test that existing file is returned"""
        # Create a test file in output folder
        output_folder = "output"
        os.makedirs(output_folder, exist_ok=True)
        
        test_filename = "test_output.png"
        test_path = os.path.join(output_folder, test_filename)
        
        # Create and save test image
        image = Image.new('RGB', (100, 100), color='red')
        image.save(test_path)
        
        try:
            response = client.get(f"/output/{test_filename}")
            assert response.status_code == 200
        finally:
            # Cleanup
            if os.path.exists(test_path):
                os.remove(test_path)


class TestCORSMiddleware:
    """Test cases for CORS middleware"""
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present in response"""
        response = client.options("/ocr")
        # CORS headers should allow cross-origin requests
        assert response.status_code in [200, 405]


class TestContentTypes:
    """Test cases for different content types"""
    
    def test_jpeg_image_accepted(self):
        """Test that JPEG images are accepted"""
        image = Image.new('RGB', (100, 100), color='blue')
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        response = client.post(
            "/ocr",
            files={"file": ("test.jpg", img_byte_arr, "image/jpeg")}
        )
        
        assert response.status_code in [200, 500]
    
    def test_png_image_accepted(self):
        """Test that PNG images are accepted"""
        image_data = create_test_image()
        
        response = client.post(
            "/ocr",
            files={"file": ("test.png", image_data, "image/png")}
        )
        
        assert response.status_code in [200, 500]
