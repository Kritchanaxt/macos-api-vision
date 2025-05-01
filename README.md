# macos-api-vision
OCR mac api face quality detection Card detection and wrap perspective

## Project Summary

| Category           | Details                                                                                     |
|--------------------|---------------------------------------------------------------------------------------------|
| Name Project       | MAC API                                                                                     |
| Main Goal          | OCR Mac, Face quality detection, Card detection, Wrap perspective                           |
| Tools              | Vision Framework (macOS), CoreImage, PyObjC, FastAPI, OpenCV, NumPy, Pillow(PIL), Uvicorn |

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
| Wrap Perspective Manual| แก้ไขภาพให้เป็นรูปตรง           | |

