import Vision
import Foundation
import Quartz
import numpy as np
import tempfile
import os
import time
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw
from app.utils.image_utils import get_image_dimensions, calculate_fast_rate, calculate_rack_cooling_rate


def detect_card(image: Image.Image) -> Dict[str, Any]:
    start_time = time.time()
    dimensions = get_image_dimensions(image)
    width, height = dimensions["width"], dimensions["height"]

    temp_filename = _save_temp_image(image)
    output_image = image.copy()
    cards = []
    max_confidence = 0.0
    best_card_position = None

    try:
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(
            Foundation.NSURL.fileURLWithPath_(temp_filename), None
        )

        cards = _detect_with_rectangle_request(handler, width, height)

        if not cards:
            cards = _detect_with_document_request(handler, width, height)

        cards, max_confidence, best_card_position = _filter_cards(cards)

        draw = ImageDraw.Draw(output_image)
        for card in cards:
            pos = card["position"]
            confidence = card["confidence"]
            color = (0, 255, 0)  # Set color to green by default
            draw.rectangle([pos["x"], pos["y"], pos["x"] + pos["width"], pos["y"] + pos["height"]],
                           outline=color, width=4)
            draw.text((pos["x"], pos["y"] - 20), f"Confidence: {confidence:.2f}", fill=color)  # Confidence text

        return {
            "has_card": len(cards) > 0,
            "card_count": len(cards),
            "document_type": "id_card" if cards else "unknown",
            "confidence": max_confidence,
            "position": best_card_position,
            "cards": cards,
            "dimensions": dimensions,
            "fast_rate": calculate_fast_rate(width, height),
            "rack_cooling_rate": calculate_rack_cooling_rate(width, height, len(cards)),
            "processing_time": time.time() - start_time,
            "output_image": output_image
        }

    except Exception as e:
        return {
            "has_card": False,
            "card_count": 0,
            "document_type": "unknown",
            "confidence": 0.0,
            "position": None,
            "error": f"Error occurred: {str(e)}",
            "cards": [],
            "dimensions": dimensions,
            "fast_rate": calculate_fast_rate(width, height),
            "rack_cooling_rate": calculate_rack_cooling_rate(width, height, 0),
            "processing_time": time.time() - start_time,
            "output_image": output_image
        }
    finally:
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)


def _save_temp_image(image):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        image.save(tmp.name, "PNG")
        return tmp.name


def _detect_with_rectangle_request(handler, width, height) -> List[Dict[str, Any]]:
    request = Vision.VNDetectRectanglesRequest.alloc().init()
    request.setMinimumAspectRatio_(0.5)
    request.setMaximumAspectRatio_(2.2)
    request.setMinimumSize_(0.15)
    request.setMaximumObservations_(5)
    request.setQuadratureTolerance_(8.0)

    success, error = handler.performRequests_error_([request], None)
    if error:
        return []

    results = []
    for i, obs in enumerate(request.results() or []):
        bbox = obs.boundingBox()
        confidence = obs.confidence()
        x, y = bbox.origin.x * width, (1.0 - bbox.origin.y - bbox.size.height) * height
        w, h = bbox.size.width * width, bbox.size.height * height
        aspect_ratio = w / h
        is_card_like = 1.3 <= aspect_ratio <= 1.9
        final_conf = confidence * (1.0 if is_card_like else 0.7)

        results.append({
            "id": f"card-{i}",
            "position": {"x": x, "y": y, "width": w, "height": h},
            "confidence": final_conf,
            "is_card_like": is_card_like,
            "aspect_ratio": aspect_ratio,
            "corners": _convert_bounding_box_to_corners(bbox, width, height)
        })
    return results


def _detect_with_document_request(handler, width, height) -> List[Dict[str, Any]]:
    request = Vision.VNDetectDocumentSegmentationRequest.alloc().init()
    success, error = handler.performRequests_error_([request], None)
    if error:
        return []

    results = []
    for i, obs in enumerate(request.results() or []):
        bbox = obs.boundingBox()
        x, y = bbox.origin.x * width, (1.0 - bbox.origin.y - bbox.size.height) * height
        w, h = bbox.size.width * width, bbox.size.height * height
        aspect_ratio = w / h
        confidence = 0.6  # Estimated for fallback

        results.append({
            "id": f"doc-{i}",
            "position": {"x": x, "y": y, "width": w, "height": h},
            "confidence": confidence,
            "is_card_like": 1.3 <= aspect_ratio <= 1.9,
            "aspect_ratio": aspect_ratio,
            "corners": _convert_bounding_box_to_corners(bbox, width, height)
        })
    return results


def _filter_cards(cards: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float, Dict[str, Any]]:
    if not cards:
        return [], 0.0, None

    cards.sort(key=lambda c: c["confidence"], reverse=True)
    best = cards[0]
    filtered = [best]

    for other in cards[1:]:
        if not _has_significant_overlap(best["position"], other["position"]):
            filtered.append(other)

    return filtered, best["confidence"], best["position"]


def _convert_bounding_box_to_corners(bbox, width, height) -> List[Dict[str, float]]:
    x, y, w, h = bbox.origin.x, bbox.origin.y, bbox.size.width, bbox.size.height
    return [
        {"x": x * width, "y": (1 - y - h) * height},
        {"x": x * width, "y": (1 - y) * height},
        {"x": (x + w) * width, "y": (1 - y) * height},
        {"x": (x + w) * width, "y": (1 - y - h) * height}
    ]


def _has_significant_overlap(b1, b2, threshold=0.7):
    x1 = max(b1["x"], b2["x"])
    y1 = max(b1["y"], b2["y"])
    x2 = min(b1["x"] + b1["width"], b2["x"] + b2["width"])
    y2 = min(b1["y"] + b1["height"], b2["y"] + b2["height"])
    if x2 <= x1 or y2 <= y1:
        return False
    inter_area = (x2 - x1) * (y2 - y1)
    union_area = b1["width"] * b1["height"] + b2["width"] * b2["height"] - inter_area
    return (inter_area / union_area) > threshold
