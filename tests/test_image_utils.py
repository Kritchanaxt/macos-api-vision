"""
Unit tests for app/utils/image_utils.py
"""
import pytest
from PIL import Image
from app.utils.image_utils import (
    get_image_dimensions,
    calculate_fast_rate,
    calculate_rack_cooling_rate
)


class TestGetImageDimensions:
    """Test cases for get_image_dimensions function"""
    
    def test_get_dimensions_from_pil_image(self):
        """Test getting dimensions from PIL Image"""
        image = Image.new('RGB', (1920, 1080))
        result = get_image_dimensions(image)
        
        assert result["width"] == 1920
        assert result["height"] == 1080
        assert result["unit"] == "pixel"
    
    def test_get_dimensions_small_image(self):
        """Test getting dimensions from small image"""
        image = Image.new('RGB', (100, 100))
        result = get_image_dimensions(image)
        
        assert result["width"] == 100
        assert result["height"] == 100
    
    def test_get_dimensions_portrait_image(self):
        """Test getting dimensions from portrait image"""
        image = Image.new('RGB', (480, 640))
        result = get_image_dimensions(image)
        
        assert result["width"] == 480
        assert result["height"] == 640
    
    def test_get_dimensions_large_image(self):
        """Test getting dimensions from large image"""
        image = Image.new('RGB', (4000, 3000))
        result = get_image_dimensions(image)
        
        assert result["width"] == 4000
        assert result["height"] == 3000


class TestCalculateFastRate:
    """Test cases for calculate_fast_rate function"""
    
    def test_fast_rate_1mp(self):
        """Test fast rate for 1 megapixel image (1000x1000)"""
        rate = calculate_fast_rate(1000, 1000)
        assert rate == 1.0
    
    def test_fast_rate_1080p(self):
        """Test fast rate for 1080p image"""
        rate = calculate_fast_rate(1920, 1080)
        expected = (1920 * 1080) / 1000000.0
        assert rate == pytest.approx(expected, rel=1e-6)
    
    def test_fast_rate_4k(self):
        """Test fast rate for 4K image"""
        rate = calculate_fast_rate(3840, 2160)
        expected = (3840 * 2160) / 1000000.0
        assert rate == pytest.approx(expected, rel=1e-6)
    
    def test_fast_rate_small_image(self):
        """Test fast rate for small image"""
        rate = calculate_fast_rate(100, 100)
        expected = 10000 / 1000000.0
        assert rate == pytest.approx(expected, rel=1e-6)
    
    def test_fast_rate_zero_dimension(self):
        """Test fast rate with zero dimension"""
        rate = calculate_fast_rate(0, 1000)
        assert rate == 0.0


class TestCalculateRackCoolingRate:
    """Test cases for calculate_rack_cooling_rate function"""
    
    def test_rack_rate_no_faces(self):
        """Test rack cooling rate with no faces"""
        rate = calculate_rack_cooling_rate(1920, 1080, 0)
        expected = (1920 + 1080) * 1.0 / 1000.0
        assert rate == pytest.approx(expected, rel=1e-6)
    
    def test_rack_rate_one_face(self):
        """Test rack cooling rate with one face"""
        rate = calculate_rack_cooling_rate(1920, 1080, 1)
        expected = (1920 + 1080) * (1 + 1/10) / 1000.0
        assert rate == pytest.approx(expected, rel=1e-6)
    
    def test_rack_rate_multiple_faces(self):
        """Test rack cooling rate with multiple faces"""
        rate = calculate_rack_cooling_rate(1920, 1080, 5)
        expected = (1920 + 1080) * (1 + 5/10) / 1000.0
        assert rate == pytest.approx(expected, rel=1e-6)
    
    def test_rack_rate_default_face_count(self):
        """Test rack cooling rate with default face count"""
        rate = calculate_rack_cooling_rate(1000, 1000)
        expected = (1000 + 1000) * 1.0 / 1000.0
        assert rate == pytest.approx(expected, rel=1e-6)
    
    def test_rack_rate_small_image(self):
        """Test rack cooling rate for small image"""
        rate = calculate_rack_cooling_rate(100, 100, 0)
        expected = 200 / 1000.0
        assert rate == pytest.approx(expected, rel=1e-6)


class TestIntegration:
    """Integration tests for image utils"""
    
    def test_dimensions_and_rates_together(self):
        """Test getting dimensions and calculating rates together"""
        image = Image.new('RGB', (1920, 1080))
        dims = get_image_dimensions(image)
        
        fast_rate = calculate_fast_rate(dims["width"], dims["height"])
        rack_rate = calculate_rack_cooling_rate(dims["width"], dims["height"], 1)
        
        assert dims["width"] == 1920
        assert dims["height"] == 1080
        assert fast_rate > 0
        assert rack_rate > 0
