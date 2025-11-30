"""
Unit tests for app/ocr/engine.py
"""
import pytest
from app.ocr.engine import organize_text_elements_into_lines


class TestOrganizeTextElementsIntoLines:
    """Test cases for organize_text_elements_into_lines function"""
    
    def test_empty_elements(self):
        """Test with empty text elements list"""
        result = organize_text_elements_into_lines([])
        assert result == {}
    
    def test_single_element(self):
        """Test with single text element"""
        elements = [
            {
                "text": "Hello",
                "confidence": 0.95,
                "position": {"x": 10, "y": 20, "width": 50, "height": 20}
            }
        ]
        result = organize_text_elements_into_lines(elements)
        
        assert len(result) == 1
        assert "line_1" in result
        assert result["line_1"]["text"] == "Hello"
        assert result["line_1"]["confidence"] == 0.95
    
    def test_multiple_elements_same_line(self):
        """Test multiple elements on the same line"""
        elements = [
            {
                "text": "Hello",
                "confidence": 0.95,
                "position": {"x": 10, "y": 20, "width": 50, "height": 20}
            },
            {
                "text": "World",
                "confidence": 0.90,
                "position": {"x": 70, "y": 22, "width": 50, "height": 20}
            }
        ]
        result = organize_text_elements_into_lines(elements)
        
        assert len(result) == 1
        assert "line_1" in result
        assert "Hello" in result["line_1"]["text"]
        assert "World" in result["line_1"]["text"]
    
    def test_multiple_elements_different_lines(self):
        """Test multiple elements on different lines"""
        elements = [
            {
                "text": "Line 1",
                "confidence": 0.95,
                "position": {"x": 10, "y": 20, "width": 50, "height": 20}
            },
            {
                "text": "Line 2",
                "confidence": 0.90,
                "position": {"x": 10, "y": 60, "width": 50, "height": 20}
            },
            {
                "text": "Line 3",
                "confidence": 0.85,
                "position": {"x": 10, "y": 100, "width": 50, "height": 20}
            }
        ]
        result = organize_text_elements_into_lines(elements)
        
        assert len(result) == 3
        assert "line_1" in result
        assert "line_2" in result
        assert "line_3" in result
    
    def test_elements_sorted_by_x_within_line(self):
        """Test that elements within a line are sorted by x coordinate"""
        elements = [
            {
                "text": "World",
                "confidence": 0.90,
                "position": {"x": 100, "y": 20, "width": 50, "height": 20}
            },
            {
                "text": "Hello",
                "confidence": 0.95,
                "position": {"x": 10, "y": 22, "width": 50, "height": 20}
            }
        ]
        result = organize_text_elements_into_lines(elements)
        
        assert result["line_1"]["text"] == "Hello World"
    
    def test_confidence_averaging(self):
        """Test that confidence is averaged for elements in same line"""
        elements = [
            {
                "text": "Hello",
                "confidence": 1.0,
                "position": {"x": 10, "y": 20, "width": 50, "height": 20}
            },
            {
                "text": "World",
                "confidence": 0.5,
                "position": {"x": 70, "y": 22, "width": 50, "height": 20}
            }
        ]
        result = organize_text_elements_into_lines(elements)
        
        assert result["line_1"]["confidence"] == 0.75
    
    def test_position_calculation(self):
        """Test that line position is calculated correctly"""
        elements = [
            {
                "text": "Hello",
                "confidence": 0.95,
                "position": {"x": 10, "y": 20, "width": 50, "height": 20}
            },
            {
                "text": "World",
                "confidence": 0.90,
                "position": {"x": 70, "y": 20, "width": 60, "height": 25}
            }
        ]
        result = organize_text_elements_into_lines(elements)
        
        # min_x should be 10
        assert result["line_1"]["position"]["x"] == 10
        # min_y should be 20
        assert result["line_1"]["position"]["y"] == 20
        # width should be max_x - min_x = (70 + 60) - 10 = 120
        assert result["line_1"]["position"]["width"] == 120
    
    def test_line_ids_sequential(self):
        """Test that line IDs are sequential"""
        elements = [
            {"text": "A", "confidence": 0.9, "position": {"x": 0, "y": 0, "width": 10, "height": 10}},
            {"text": "B", "confidence": 0.9, "position": {"x": 0, "y": 30, "width": 10, "height": 10}},
            {"text": "C", "confidence": 0.9, "position": {"x": 0, "y": 60, "width": 10, "height": 10}},
            {"text": "D", "confidence": 0.9, "position": {"x": 0, "y": 90, "width": 10, "height": 10}},
        ]
        result = organize_text_elements_into_lines(elements)
        
        assert "line_1" in result
        assert "line_2" in result
        assert "line_3" in result
        assert "line_4" in result
    
    def test_thai_text_elements(self):
        """Test with Thai text elements"""
        elements = [
            {
                "text": "สวัสดี",
                "confidence": 0.95,
                "position": {"x": 10, "y": 20, "width": 60, "height": 25}
            },
            {
                "text": "ครับ",
                "confidence": 0.90,
                "position": {"x": 80, "y": 22, "width": 40, "height": 25}
            }
        ]
        result = organize_text_elements_into_lines(elements)
        
        assert "สวัสดี" in result["line_1"]["text"]
        assert "ครับ" in result["line_1"]["text"]
    
    def test_line_grouping_threshold(self):
        """Test the line grouping threshold of 20 pixels"""
        elements = [
            # These two should be on the same line (within 20px)
            {"text": "A", "confidence": 0.9, "position": {"x": 0, "y": 0, "width": 10, "height": 10}},
            {"text": "B", "confidence": 0.9, "position": {"x": 20, "y": 15, "width": 10, "height": 10}},
            # This should be on a different line (more than 20px difference)
            {"text": "C", "confidence": 0.9, "position": {"x": 0, "y": 40, "width": 10, "height": 10}},
        ]
        result = organize_text_elements_into_lines(elements)
        
        assert len(result) == 2
        assert "A" in result["line_1"]["text"]
        assert "B" in result["line_1"]["text"]
        assert result["line_2"]["text"] == "C"
