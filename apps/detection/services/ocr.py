"""
Optical Character Recognition (OCR) Service for Netra.
Extracts street signage, bus route numbers, storefront names, and text in English and Hindi.
Runs in a managed ThreadPoolExecutor to prevent blocking asynchronous WebSocket and HTTP loops.
"""
import concurrent.futures
from typing import List, Dict, Any
from PIL import Image

from .constants import DIRECTION_THRESHOLDS

ocr_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="netra_ocr")


def determine_ocr_direction(box: List[float]) -> str:
    """
    Computes horizontal direction ('left', 'ahead', 'right') for normalized box [x, y, w, h].
    """
    cx = box[0] + (box[2] / 2.0)
    if cx < DIRECTION_THRESHOLDS["left_limit"]:
        return "left"
    elif cx > DIRECTION_THRESHOLDS["right_limit"]:
        return "right"
    return "ahead"


def _process_image_ocr(image: Image.Image, language: str = "en") -> List[Dict[str, Any]]:
    """
    Internal synchronous OCR runner.
    """
    blocks: List[Dict[str, Any]] = []
    width, height = image.size
    if width <= 0 or height <= 0:
        return blocks

    try:
        import pytesseract
        from pytesseract import Output

        # Map languages for tesseract: eng, hin, or eng+hin
        lang_str = "hin+eng" if language in ("hi", "hin") else "eng"

        try:
            data = pytesseract.image_to_data(image, lang=lang_str, output_type=Output.DICT)
        except Exception:
            # Fallback to English if Hindi language pack is missing from Tesseract installation
            data = pytesseract.image_to_data(image, lang="eng", output_type=Output.DICT)

        n_boxes = len(data.get("text", []))
        for i in range(n_boxes):
            word = str(data["text"][i]).strip()
            conf = float(data["conf"][i])

            # Filter low confidence or whitespace noise
            if word and conf > 30.0:
                bx = float(data["left"][i]) / width
                by = float(data["top"][i]) / height
                bw = float(data["width"][i]) / width
                bh = float(data["height"][i]) / height

                box_norm = [
                    round(max(0.0, min(1.0, bx)), 4),
                    round(max(0.0, min(1.0, by)), 4),
                    round(max(0.0, min(1.0, bw)), 4),
                    round(max(0.0, min(1.0, bh)), 4),
                ]

                blocks.append({
                    "text": word,
                    "confidence": round(conf / 100.0, 2),
                    "box": box_norm,
                    "direction": determine_ocr_direction(box_norm),
                })
    except Exception as e:
        # Graceful fallback: return empty blocks if system tesseract is unavailable
        # In unit tests or mock environments, custom handler can supply results
        pass

    return blocks


def run_ocr(image: Image.Image, language: str = "en") -> concurrent.futures.Future:
    """
    Submits an OCR extraction task to the background thread pool and returns a Future.
    """
    return ocr_executor.submit(_process_image_ocr, image, language)
