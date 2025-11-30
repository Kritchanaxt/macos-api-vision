"""
Unit tests for app/ocr/document_classifier.py
"""
import pytest
from app.ocr.document_classifier import classify_document_type


class TestThaiIDCardClassification:
    """Test cases for Thai ID card classification"""
    
    def test_thai_id_card_by_text(self):
        """Test classification by Thai ID card text"""
        text = "บัตรประจำตัวประชาชน"
        result = classify_document_type(text, [])
        assert result == "card_id"
    
    def test_thai_id_card_by_english_text(self):
        """Test classification by English ID card text"""
        text = "Thai National ID Card"
        result = classify_document_type(text, [])
        assert result == "card_id"
    
    def test_thai_id_by_13_digit_number(self):
        """Test classification by 13-digit ID number"""
        text = "รหัส: 1234567890123"
        result = classify_document_type(text, [])
        assert result == "card_id"
    
    def test_thai_id_by_formatted_number(self):
        """Test classification by formatted ID number with dashes"""
        text = "เลขบัตร: 1-2345-67890-12-3"
        result = classify_document_type(text, [])
        assert result == "card_id"
    
    def test_identification_card_text(self):
        """Test classification by 'identification card' text"""
        text = "identification card thailand"
        result = classify_document_type(text, [])
        assert result == "card_id"


class TestPassportClassification:
    """Test cases for passport classification"""
    
    def test_passport_by_english_text(self):
        """Test classification by English passport text"""
        text = "PASSPORT"
        result = classify_document_type(text, [])
        assert result == "passport"
    
    def test_passport_by_thai_text(self):
        """Test classification by Thai passport text"""
        text = "หนังสือเดินทาง"
        result = classify_document_type(text, [])
        assert result == "passport"
    
    def test_passport_by_nationality(self):
        """Test classification by nationality field"""
        text = "Nationality: Thai"
        result = classify_document_type(text, [])
        assert result == "passport"
    
    def test_passport_by_thai_nationality(self):
        """Test classification by Thai nationality text"""
        text = "สัญชาติ ไทย"
        result = classify_document_type(text, [])
        assert result == "passport"


class TestDrivingLicenseClassification:
    """Test cases for driving license classification"""
    
    def test_driving_licence_uk_spelling(self):
        """Test classification by UK spelling"""
        text = "Driving Licence"
        result = classify_document_type(text, [])
        assert result == "driving_license"
    
    def test_driver_license_us_spelling(self):
        """Test classification by US spelling"""
        text = "Driver's License"
        result = classify_document_type(text, [])
        assert result == "driving_license"
    
    def test_driver_license_without_apostrophe(self):
        """Test classification without apostrophe"""
        text = "Driver License"
        result = classify_document_type(text, [])
        assert result == "driving_license"
    
    def test_thai_driving_license(self):
        """Test classification by Thai text"""
        text = "ใบอนุญาตขับขี่"
        result = classify_document_type(text, [])
        assert result == "driving_license"
    
    def test_thai_driving_license_short(self):
        """Test classification by short Thai text"""
        text = "ใบขับขี่"
        result = classify_document_type(text, [])
        assert result == "driving_license"


class TestUnknownDocuments:
    """Test cases for unknown document classification"""
    
    def test_empty_text(self):
        """Test classification with empty text"""
        result = classify_document_type("", [])
        assert result == "unknown"
    
    def test_random_text(self):
        """Test classification with random text"""
        text = "Hello World, this is some random text"
        result = classify_document_type(text, [])
        assert result == "unknown"
    
    def test_numbers_only(self):
        """Test classification with only numbers (not ID format)"""
        text = "12345 67890"
        result = classify_document_type(text, [])
        assert result == "unknown"
    
    def test_thai_random_text(self):
        """Test classification with random Thai text"""
        text = "สวัสดีครับ วันนี้อากาศดี"
        result = classify_document_type(text, [])
        assert result == "unknown"


class TestTextElementsAnalysis:
    """Test cases for text elements analysis"""
    
    def test_classification_by_name_pattern(self):
        """Test classification by name pattern in text elements"""
        text = "document info"
        text_elements = [
            {"text": "นาย สมชาย ใจดี", "confidence": 0.9, "position": {"x": 0, "y": 0}},
            {"text": "Address", "confidence": 0.9, "position": {"x": 0, "y": 20}},
            {"text": "Line 3", "confidence": 0.9, "position": {"x": 0, "y": 40}},
            {"text": "Line 4", "confidence": 0.9, "position": {"x": 0, "y": 60}},
            {"text": "Line 5", "confidence": 0.9, "position": {"x": 0, "y": 80}},
            {"text": "Line 6", "confidence": 0.9, "position": {"x": 0, "y": 100}},
        ]
        result = classify_document_type(text, text_elements)
        assert result == "card_id"
    
    def test_classification_by_date_pattern(self):
        """Test classification by date of birth pattern"""
        text = "document info"
        text_elements = [
            {"text": "เกิดวันที่ 1 มกราคม 2530", "confidence": 0.9, "position": {"x": 0, "y": 0}},
            {"text": "Line 2", "confidence": 0.9, "position": {"x": 0, "y": 20}},
            {"text": "Line 3", "confidence": 0.9, "position": {"x": 0, "y": 40}},
            {"text": "Line 4", "confidence": 0.9, "position": {"x": 0, "y": 60}},
            {"text": "Line 5", "confidence": 0.9, "position": {"x": 0, "y": 80}},
            {"text": "Line 6", "confidence": 0.9, "position": {"x": 0, "y": 100}},
        ]
        result = classify_document_type(text, text_elements)
        assert result == "card_id"
    
    def test_insufficient_text_elements(self):
        """Test with insufficient text elements"""
        text = "some text"
        text_elements = [
            {"text": "นาย สมชาย", "confidence": 0.9, "position": {"x": 0, "y": 0}},
            {"text": "Line 2", "confidence": 0.9, "position": {"x": 0, "y": 20}},
        ]
        result = classify_document_type(text, text_elements)
        assert result == "unknown"


class TestCaseInsensitivity:
    """Test case insensitivity of classification"""
    
    def test_uppercase_passport(self):
        """Test uppercase PASSPORT text"""
        result = classify_document_type("PASSPORT", [])
        assert result == "passport"
    
    def test_lowercase_passport(self):
        """Test lowercase passport text"""
        result = classify_document_type("passport", [])
        assert result == "passport"
    
    def test_mixed_case_driving(self):
        """Test mixed case driving text"""
        result = classify_document_type("DriViNg LiCeNcE", [])
        assert result == "driving_license"
