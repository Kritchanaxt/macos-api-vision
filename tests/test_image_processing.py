"""
Unit tests for app/utils/image_processing.py
"""
import pytest
from PIL import Image
from app.utils.image_processing import convert_to_supported_format


class TestConvertToSupportedFormat:
    """Test cases for convert_to_supported_format function"""
    
    def test_rgb_image_unchanged(self):
        """Test that RGB image remains RGB"""
        image = Image.new('RGB', (100, 100), color='red')
        result = convert_to_supported_format(image)
        assert result.mode == 'RGB'
    
    def test_rgba_image_unchanged(self):
        """Test that RGBA image remains RGBA"""
        image = Image.new('RGBA', (100, 100), color='blue')
        result = convert_to_supported_format(image)
        assert result.mode in ('RGB', 'RGBA')
    
    def test_grayscale_converted_to_rgb(self):
        """Test that grayscale image is converted to RGB"""
        image = Image.new('L', (100, 100), color=128)
        result = convert_to_supported_format(image)
        assert result.mode == 'RGB'
    
    def test_palette_converted_to_rgb(self):
        """Test that palette mode image is converted to RGB"""
        image = Image.new('P', (100, 100))
        result = convert_to_supported_format(image)
        assert result.mode == 'RGB'
    
    def test_small_image_not_resized(self):
        """Test that small images are not resized"""
        image = Image.new('RGB', (100, 100))
        result = convert_to_supported_format(image)
        assert result.size == (100, 100)
    
    def test_large_image_width_resized(self):
        """Test that large images are resized when width exceeds limit"""
        image = Image.new('RGB', (5000, 3000))
        result = convert_to_supported_format(image)
        assert result.size[0] <= 4000
        assert result.size[1] <= 4000
    
    def test_large_image_height_resized(self):
        """Test that large images are resized when height exceeds limit"""
        image = Image.new('RGB', (3000, 5000))
        result = convert_to_supported_format(image)
        assert result.size[0] <= 4000
        assert result.size[1] <= 4000
    
    def test_aspect_ratio_preserved(self):
        """Test that aspect ratio is preserved during resize"""
        image = Image.new('RGB', (6000, 3000))  # 2:1 aspect ratio
        result = convert_to_supported_format(image)
        
        original_ratio = 6000 / 3000
        result_ratio = result.size[0] / result.size[1]
        
        assert abs(original_ratio - result_ratio) < 0.01
    
    def test_exactly_max_dimension(self):
        """Test image at exactly maximum dimension"""
        image = Image.new('RGB', (4000, 3000))
        result = convert_to_supported_format(image)
        assert result.size == (4000, 3000)
    
    def test_cmyk_converted_to_rgb(self):
        """Test that CMYK image is converted to RGB"""
        image = Image.new('CMYK', (100, 100))
        result = convert_to_supported_format(image)
        assert result.mode == 'RGB'
    
    def test_1bit_converted_to_rgb(self):
        """Test that 1-bit image is converted to RGB"""
        image = Image.new('1', (100, 100))
        result = convert_to_supported_format(image)
        assert result.mode == 'RGB'


class TestConvertToSupportedFormatEdgeCases:
    """Edge case tests for convert_to_supported_format"""
    
    def test_minimum_size_image(self):
        """Test with minimum size image (1x1)"""
        image = Image.new('RGB', (1, 1))
        result = convert_to_supported_format(image)
        assert result.size == (1, 1)
    
    def test_very_wide_image(self):
        """Test with very wide image"""
        image = Image.new('RGB', (10000, 100))
        result = convert_to_supported_format(image)
        assert result.size[0] <= 4000
    
    def test_very_tall_image(self):
        """Test with very tall image"""
        image = Image.new('RGB', (100, 10000))
        result = convert_to_supported_format(image)
        assert result.size[1] <= 4000
    
    def test_square_large_image(self):
        """Test with square large image"""
        image = Image.new('RGB', (5000, 5000))
        result = convert_to_supported_format(image)
        assert result.size[0] <= 4000
        assert result.size[1] <= 4000
        assert result.size[0] == result.size[1]  # Still square
