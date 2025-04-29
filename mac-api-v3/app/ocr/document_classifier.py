from typing import List, Dict, Any
import re

def classify_document_type(text: str, text_elements: List[Dict]) -> str:
    """
    Classify the document type based on its content and format
    
    Returns one of:
    - "card_id" (Thai national ID)
    - "passport"
    - "driving_license"
    - "unknown"
    """
    text = text.lower()
    
    # Check for Thai ID card
    thai_id_patterns = [
        r"บัตรประจำตัวประชาชน",
        r"identification card",
        r"thai national id",
        r"\d-\d{4}-\d{5}-\d{2}-\d",  # ID format with dashes
        r"\d{13}"  # 13 consecutive digits
    ]
    
    for pattern in thai_id_patterns:
        if re.search(pattern, text):
            return "card_id"
    
    # Check for passport
    passport_patterns = [
        r"passport",
        r"หนังสือเดินทาง",
        r"nationality",
        r"สัญชาติ"
    ]
    
    for pattern in passport_patterns:
        if re.search(pattern, text):
            return "passport"
    
    # Check for driving license
    driving_patterns = [
        r"driving licence",
        r"driver('s)? license",
        r"ใบอนุญาตขับขี่",
        r"ใบขับขี่"
    ]
    
    for pattern in driving_patterns:
        if re.search(pattern, text):
            return "driving_license"
    
    # Analyze layout based on text elements
    if text_elements and len(text_elements) > 5:
        # Check for ID card format (usually has structured layout with name, ID number, etc.)
        # Look for name fields, birth date, issue date - common in ID cards
        name_patterns = [r"name", r"ชื่อ", r"นาย", r"นาง", r"นางสาว"]
        date_patterns = [r"เกิดวันที่", r"date of birth", r"issue", r"วันออกบัตร"]
        
        for pattern in name_patterns + date_patterns:
            for element in text_elements:
                if re.search(pattern, element["text"].lower()):
                    return "card_id"  # Most likely an ID card if it has name and date fields
    
    return "unknown"