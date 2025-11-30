"""
Pytest configuration and fixtures for macos-api-vision tests
"""
import pytest
import os
import sys
from PIL import Image
import io

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_rgb_image():
    """Create a sample RGB image for testing"""
    return Image.new('RGB', (800, 600), color='white')


@pytest.fixture
def sample_rgba_image():
    """Create a sample RGBA image for testing"""
    return Image.new('RGBA', (800, 600), color='white')


@pytest.fixture
def sample_grayscale_image():
    """Create a sample grayscale image for testing"""
    return Image.new('L', (800, 600), color=128)


@pytest.fixture
def sample_large_image():
    """Create a sample large image for testing resize"""
    return Image.new('RGB', (5000, 4000), color='white')


@pytest.fixture
def sample_text_elements():
    """Create sample text elements for OCR testing"""
    return [
        {
            "text": "Hello",
            "confidence": 0.95,
            "position": {"x": 10, "y": 20, "width": 50, "height": 20}
        },
        {
            "text": "World",
            "confidence": 0.90,
            "position": {"x": 70, "y": 22, "width": 50, "height": 20}
        },
        {
            "text": "Line 2",
            "confidence": 0.85,
            "position": {"x": 10, "y": 60, "width": 60, "height": 20}
        }
    ]


@pytest.fixture
def sample_thai_text_elements():
    """Create sample Thai text elements for OCR testing"""
    return [
        {
            "text": "สวัสดี",
            "confidence": 0.92,
            "position": {"x": 10, "y": 20, "width": 60, "height": 25}
        },
        {
            "text": "ครับ",
            "confidence": 0.88,
            "position": {"x": 80, "y": 22, "width": 40, "height": 25}
        }
    ]


@pytest.fixture
def sample_image_bytes():
    """Create sample image bytes for API testing"""
    image = Image.new('RGB', (100, 100), color='white')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr


@pytest.fixture
def output_directory(tmp_path):
    """Create a temporary output directory for testing"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_id_card_text():
    """Sample text from a Thai ID card"""
    return """
    บัตรประจำตัวประชาชน
    Thai National ID Card
    ชื่อ นาย สมชาย ใจดี
    เกิดวันที่ 1 มกราคม 2530
    1-2345-67890-12-3
    """


@pytest.fixture
def sample_passport_text():
    """Sample text from a passport"""
    return """
    PASSPORT
    หนังสือเดินทาง
    Nationality: Thai
    สัญชาติ ไทย
    """


@pytest.fixture
def sample_driving_license_text():
    """Sample text from a driving license"""
    return """
    ใบอนุญาตขับขี่
    Driving Licence
    ชื่อ นาย สมชาย
    """


# Markers for skipping tests on non-macOS
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "macos_only: mark test as requiring macOS"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Skip macOS-only tests on other platforms"""
    import platform
    
    if platform.system() != "Darwin":
        skip_macos = pytest.mark.skip(reason="Test requires macOS")
        for item in items:
            if "macos_only" in item.keywords:
                item.add_marker(skip_macos)
