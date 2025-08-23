# macos-api-vision
OCR mac api face quality detection Card detection and wrap perspective

## Project Summary

| Category           | Details                                                                                     |
|--------------------|---------------------------------------------------------------------------------------------|
| Name Project       | MAC API                                                                                     |
| Main Goal          | OCR Mac, Face quality detection, Card detection, Wrap perspective                           |
| Tools              | Vision Framework (macOS), CoreImage, PyObjC, FastAPI, NumPy, Pillow(PIL) |

---

## Repository OCR Comparison

| Name                | URL                                                             | Status     | OCR Summary                                      |
|---------------------|------------------------------------------------------------------|------------|--------------------------------------------------|
| ocrmac              | [GitHub](https://github.com/straussmaximilian/ocrmac)           | ❌ ล้มเหลว | ไม่รองรับภาษาไทย, ไม่ flexible                  |
| mac-ocr-cli         | [GitHub](https://github.com/dielect/mac-ocr-cli)                | ❌ ล้มเหลว | ไม่รองรับภาพซับซ้อน, OCR พลาดบ่อย              |
| macos-vision-ocr    | [GitHub](https://github.com/bytefer/macos-vision-ocr)           | ✅ ใช้ได้  | รองรับ Vision และ ภาษาไทย                       |

---

## Feature Overview

| Feature                 | Details                          | USE API                                                                 |
|-------------------------|----------------------------------|-------------------------------------------------------------------------|
| OCR                    | ตรวจจับข้อความในภาพ             | `VNRecognizeTextRequest`                                                |
| Face Quality Detection | ตรวจจับใบหน้าและคุณภาพ          | `VNDetectFaceRectanglesRequest`                                        |
| Card Detection         | ตรวจจับบัตรในภาพ                 | `VNDetectRectanglesRequest`                                            |
| Wrap Perspective | แก้ไขภาพให้เป็นรูปตรง           | `VNDetectRectanglesRequest, VNImageRequestHandler, CIPerspectiveCorrection, CIImage` |

---

## 📋 System Requirements

- **Operating System**: macOS 10.15 (Catalina) หรือใหม่กว่า
- **Python**: Python 3.8 หรือใหม่กว่า
- **Xcode Command Line Tools**: สำหรับการคอมไพล์ PyObjC
- **RAM**: แนะนำอย่างน้อย 4GB
- **Storage**: อย่างน้อย 500MB สำหรับ dependencies

---

## 🚀 Installation Guide

### 1. Clone Repository
```bash
git clone https://github.com/Kritchanaxt/macos-api-vision.git
cd macos-api-vision
```

### 2. ติดตั้ง Dependencies
```bash
# ติดตั้ง packages ที่จำเป็น
pip install -r requirements.txt
```

### 3. ติดตั้ง Xcode Command Line Tools (ถ้ายังไม่ได้ติดตั้ง)
```bash
xcode-select --install
```

### 4. ตรวจสอบการติดตั้ง
```bash
# ตรวจสอบ Python version
python3 --version

# ตรวจสอบ PyObjC
python3 -c "import objc; print('PyObjC installed successfully')"
```

---

## 🏃‍♂️ Getting Started

### เริ่มต้นใช้งาน API Server

```bash
# รัน FastAPI server
fastapi dev app/main.py
```

API จะเริ่มทำงานที่: `http://localhost:8000`

### เข้าถึง API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🔧 API Usage Examples

### 1. OCR (Text Recognition)

**Endpoint**: `POST /ocr`

**Parameters**:
- `file`: ไฟล์รูปภาพ (jpg, png, heic, etc.)
- `languages`: ภาษาที่ต้องการตรวจจับ (default: "th-TH,en-US")
- `recognition_level`: ระดับความแม่นยำ ("fast" หรือ "accurate")
- `save_visualization`: บันทึกภาพผลลัพธ์หรือไม่ (true/false)

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/ocr" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/your/image.jpg" \
  -F "languages=th-TH,en-US" \
  -F "recognition_level=accurate" \
  -F "save_visualization=true"
```

**Response Example**:
```json
{
  "success": true,
  "text_elements": [
    {
      "text": "ข้อสอบ 5 ข้อ",
      "confidence": 0.95,
      "bounding_box": {
        "top_left": {"x": 112, "y": 100},
        "top_right": {"x": 300, "y": 100},
        "bottom_left": {"x": 112, "y": 150},
        "bottom_right": {"x": 300, "y": 150}
      }
    }
  ],
  "full_text": "ข้อสอบ 5 ข้อ\n1. Algebra SQL\n2. ER, Normalize\n3. Concept Structure",
  "image_dimensions": {"width": 1024, "height": 768},
  "visualization_url": "http://localhost:8000/output/ocr_20250823_123456_abc123.png"
}
```

### 2. Face Quality Detection

**Endpoint**: `POST /face-quality`

**Parameters**:
- `file`: ไฟล์รูปภาพ
- `save_visualization`: บันทึกภาพผลลัพธ์หรือไม่

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/face-quality" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/your/face_image.jpg" \
  -F "save_visualization=true"
```

**Response Example**:
```json
{
  "success": true,
  "faces_detected": 1,
  "faces": [
    {
      "bounding_box": {
        "top_left": {"x": 150, "y": 100},
        "top_right": {"x": 350, "y": 100},
        "bottom_left": {"x": 150, "y": 300},
        "bottom_right": {"x": 350, "y": 300}
      },
      "confidence": 0.98,
      "quality_score": 0.92,
      "face_quality": "high"
    }
  ],
  "image_dimensions": {"width": 800, "height": 600},
  "visualization_url": "http://localhost:8000/output/face_20250823_123456_def456.png"
}
```

### 3. Card Detection

**Endpoint**: `POST /card-detect`

**Parameters**:
- `file`: ไฟล์รูปภาพ
- `save_visualization`: บันทึกภาพผลลัพธ์หรือไม่

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/card-detect" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/your/card_image.jpg" \
  -F "save_visualization=true"
```

**Response Example**:
```json
{
  "has_card": true,
  "card_count": 1,
  "document_type": "id_card",
  "confidence": 0.7,
  "position": {
    "x": 114.3058180063963,
    "y": 38.604116678237915,
    "width": 937.8973341733217,
    "height": 1482.1484567150474
  },
  "dimensions": {
    "width": 1170,
    "height": 1564,
    "unit": "pixel"
  },
  "fast_rate": 1.82988,
  "rack_cooling_rate": 3.0074,
  "processing_time": 0.287661075592041,
  "output_path": "/output/card_20250823_222941_bc247d27.png"
}
```

### 4. Perspective Correction (Document Wrap)

**Endpoint**: `POST /perspective`

**Parameters**:
- `file`: ไฟล์รูปภาพ
- `corners`: มุม 4 จุดของเอกสาร (optional - ถ้าไม่ระบุจะใช้ auto-detection)
- `enhance`: ปรับปรุงคุณภาพภาพหรือไม่
- `save_visualization`: บันทึกภาพผลลัพธ์หรือไม่

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/perspective" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/your/document.jpg" \
  -F "enhance=true" \
  -F "save_visualization=true"
```

**Manual Corner Detection**:
```bash
curl -X POST "http://localhost:8000/perspective/detect-rectangle" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/your/document.jpg"
```

---

## 🖥️ Web Interface

โปรเจ็กต์มีเว็บอินเตอร์เฟซสำหรับ Perspective Correction:

```bash
# เปิดไฟล์ web interface ในเบราว์เซอร์
open web-wrap-perspective/index.html
```

**หรือ** รันผ่าน HTTP server:
```bash
cd web-wrap-perspective
python3 -m http.server 3000
# เปิดเบราว์เซอร์ไปที่ http://localhost:3000
```

---

## 📁 Project Structure

```
macos-api-vision/
├── app/
│   ├── main.py              # FastAPI main application
│   ├── card/                # Card detection module
│   ├── face/                # Face quality detection module
│   ├── models/              # Pydantic schemas
│   ├── ocr/                 # OCR engine and document classifier
│   ├── utils/               # Utility functions
│   └── wrap/                # Perspective correction module
├── output/                  # Generated output files
├── static/                  # Static files for web interface
├── web-wrap-perspective/    # Web interface for perspective correction
├── requirements.txt         # Python dependencies
└── README.md               # This documentation
```

---

## 🔍 Supported File Formats

- **รูปภาพ**: JPG, JPEG, PNG, HEIC, TIFF, BMP
- **ขนาดไฟล์**: สูงสุด 10MB (สามารถปรับได้ในโค้ด)
- **ความละเอียด**: แนะนำ 300-2400 pixels สำหรับผลลัพธ์ที่ดีที่สุด

---

## ⚠️ Known Issues & Solutions

### 1. PyObjC Installation Issues
```bash
# ถ้าเกิดข้อผิดพลาดในการติดตั้ง PyObjC
pip install --upgrade pip setuptools wheel
pip install pyobjc-core pyobjc
```

### 2. Permission Issues on macOS
```bash
# ให้สิทธิ์การเข้าถึงไฟล์
chmod +x app/main.py
```

### 3. Vision Framework Errors
- ตุรวจสอบว่าใช้ macOS 10.15 หรือใหม่กว่า
- อาจต้อง restart terminal หลังติดตั้ง Xcode Command Line Tools

