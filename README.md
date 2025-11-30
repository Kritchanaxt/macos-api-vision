# macos-api-vision
OCR mac api face quality detection Card detection and wrap perspective

![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![macOS](https://img.shields.io/badge/macOS-10.15+-000000?logo=apple&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8.0-5C3EE8?logo=opencv&logoColor=white)
![Vision Framework](https://img.shields.io/badge/Vision_Framework-macOS-purple)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![CI/CD](https://img.shields.io/badge/CI/CD-GitHub_Actions-2088FF?logo=github-actions&logoColor=white)



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
pip3 install -r requirements.txt
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
# รัน FastAPI server ด้วย uvicorn
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# หรือใช้คำสั่งสั้น
uvicorn app.main:app --reload
```

API จะเริ่มทำงานที่: `http://localhost:8000`

### เข้าถึง API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🐳 Docker

### Build Docker Image

```bash
# Build image
docker build -t fastapi-docker-app .

# Build with specific target
docker build --target production -t fastapi-docker-app .
```

### Run Container

```bash
# Run container
docker run -d --name fastapi-app -p 5000:5000 fastapi-docker-app

# Run with environment variables
docker run -d --name fastapi-app \
  -p 5000:5000 \
  -e ENV=production \
  fastapi-docker-app

# View logs
docker logs -f fastapi-app
```

### Docker Compose (Optional)

```yaml
version: '3.8'
services:
  api:
    build:
      context: .
      target: production
    ports:
      - "5000:5000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"]
      interval: 30s
      timeout: 30s
      retries: 3
```

---

## 🔄 CI/CD Pipeline

โปรเจ็กต์นี้ใช้ **GitHub Actions** สำหรับ CI/CD pipeline

### Workflow Overview

| Stage | Description | Trigger |
|-------|-------------|---------|
| **Build & Test** | ติดตั้ง dependencies และรัน tests | Push/PR to `main`, `develop` |
| **Build Docker** | Build และ push Docker image ไปยัง Docker Hub | หลังจาก Build & Test สำเร็จ |
| **Deploy DEV** | Deploy ไปยัง development environment | Push to `develop` |
| **Deploy PROD** | Deploy ไปยัง production (ต้อง approval) | Push to `main` |
| **Rollback** | Rollback ไปยัง version ก่อนหน้า | Manual trigger |

### Environment Variables (GitHub Secrets)

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |
| `N8N_WEBHOOK_URL` | n8n webhook URL สำหรับ notifications |

### Manual Deployment

```bash
# Trigger workflow manually via GitHub CLI
gh workflow run main.yml -f action="Build & Deploy"

# Rollback to specific version
gh workflow run main.yml -f action="Rollback" -f rollback_tag="dev-123" -f rollback_target="dev"
```

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
│   │   ├── __init__.py
│   │   └── detector.py      # Card/rectangle detection logic
│   ├── face/                # Face quality detection module
│   │   ├── __init__.py
│   │   └── quality_detection.py  # Face detection and quality analysis
│   ├── models/              # Pydantic schemas
│   │   ├── __init__.py
│   │   └── schemas.py       # Response/Request models
│   ├── ocr/                 # OCR engine and document classifier
│   │   ├── __init__.py
│   │   ├── document_classifier.py  # Document type classification
│   │   ├── engine.py        # OCR processing engine
│   │   └── vision_ocr.py    # macOS Vision OCR integration
│   ├── utils/               # Utility functions
│   │   ├── __init__.py
│   │   ├── image_processing.py  # Image format conversion
│   │   └── image_utils.py   # Image dimension utilities
│   └── wrap/                # Perspective correction module
│       ├── __init__.py
│       ├── correct_perspective.py  # Perspective transformation
│       ├── detect_rectangle.py     # Document edge detection
│       └── enhance_image.py        # Image enhancement filters
├── tests/                   # Unit tests
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_api_endpoints.py     # API endpoint tests
│   ├── test_document_classifier.py  # Document classifier tests
│   ├── test_image_processing.py  # Image processing tests
│   ├── test_image_utils.py       # Image utility tests
│   ├── test_ocr_engine.py        # OCR engine tests
│   └── test_schemas.py           # Schema validation tests
├── output/                  # Generated output files
├── static/                  # Static files for web interface
│   └── index.html           # API welcome page
├── web-wrap-perspective/    # Web interface for perspective correction
│   ├── index.html
│   ├── index.css
│   └── index.js
├── .github/
│   └── workflows/
│       └── main.yml         # GitHub Actions CI/CD workflow
├── Dockerfile               # Docker build configuration
├── .gitignore               # Git ignore patterns
├── requirements.txt         # Python dependencies
├── pytest.ini              # Pytest configuration
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

---

## 🧪 Testing

### รัน Unit Tests

```bash
# รัน tests ทั้งหมด
python3 -m pytest tests/ -v

# รัน tests เฉพาะไฟล์
python3 -m pytest tests/test_schemas.py -v

# รัน tests พร้อม coverage report
python3 -m pytest tests/ -v --cov=app
```

### Test Summary

| ไฟล์ Test | จำนวน Tests | ทดสอบ |
|-----------|-------------|-------|
| `test_schemas.py` | 18 | Pydantic schemas validation |
| `test_image_utils.py` | 15 | Image dimension & rate calculations |
| `test_document_classifier.py` | 24 | Document type classification (ID, Passport, etc.) |
| `test_ocr_engine.py` | 10 | OCR text line organization |
| `test_image_processing.py` | 15 | Image format conversion & resizing |
| `test_api_endpoints.py` | 19 | FastAPI endpoints integration |
| **รวม** | **101** | - |

### ติดตั้ง Testing Dependencies

```bash
pip3 install pytest httpx
```

---

## 📊 API Response Models

### OCRResponse
| Field | Type | Description |
|-------|------|-------------|
| `document_type` | string | ประเภทเอกสาร (card_id, passport, driving_license, unknown) |
| `recognized_text` | string | ข้อความที่ OCR ได้ |
| `confidence` | float | ความมั่นใจ (0.0-1.0) |
| `text_lines` | Dict | บรรทัดข้อความพร้อมตำแหน่ง |
| `dimensions` | ImageDimensions | ขนาดภาพ |
| `processing_time` | float | เวลาประมวลผล (วินาที) |

### FaceQualityResponse
| Field | Type | Description |
|-------|------|-------------|
| `has_face` | bool | พบใบหน้าหรือไม่ |
| `face_count` | int | จำนวนใบหน้าที่พบ |
| `quality_score` | float | คะแนนคุณภาพใบหน้า (0.0-1.0) |
| `position` | Dict | ตำแหน่งใบหน้า |
| `dimensions` | ImageDimensions | ขนาดภาพ |

### CardDetectionResponse
| Field | Type | Description |
|-------|------|-------------|
| `has_card` | bool | พบบัตรหรือไม่ |
| `card_count` | int | จำนวนบัตรที่พบ |
| `document_type` | string | ประเภทเอกสาร |
| `confidence` | float | ความมั่นใจ (0.0-1.0) |
| `position` | Dict | ตำแหน่งบัตร |

---

## 🔧 Configuration

### Image Processing Settings

ใน `app/utils/image_processing.py`:
- **Max Dimension**: 4000 pixels (ปรับได้)
- **Supported Modes**: RGB, RGBA

### OCR Settings

ใน `/ocr` endpoint:
- **Default Languages**: `th-TH,en-US`
- **Recognition Levels**: `fast`, `accurate`

### Docker Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONDONTWRITEBYTECODE` | `1` | ไม่สร้าง `.pyc` files |
| `PYTHONUNBUFFERED` | `1` | Output ไม่ถูก buffer |

---

## 🏥 Health Check

API มี health check endpoint สำหรับ container orchestration:

```bash
# Check health status (Docker)
curl http://localhost:5000/health

# Check health status (Local development)
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "version": "1.7.0"
}
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 👨‍💻 Author

**Kritchanaxt**
- GitHub: [@Kritchanaxt](https://github.com/Kritchanaxt)
