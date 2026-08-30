import pytesseract
from PIL import Image
import io
import os
import base64
import requests
import cv2
import numpy as np


def _preprocess_image(image_bytes: bytes) -> Image.Image:
    # Load into OpenCV
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        # fallback to PIL
        return Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Convert to gray, denoise and threshold
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, h=10)
    h, w = gray.shape
    if max(h, w) < 2000:
        scale = 1600 / max(h, w)
        if scale > 1:
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    pil = Image.fromarray(th)
    return pil


def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from image bytes. Uses Mathpix if MATHPIX_KEY is set, otherwise pytesseract."""
    mathpix_key = os.environ.get("MATHPIX_KEY")
    if mathpix_key:
        try:
            # Mathpix expects base64 and returns structured JSON
            b64 = base64.b64encode(image_bytes).decode("utf-8")
            headers = {
                "app_id": os.environ.get("MATHPIX_APP_ID", ""),
                "app_key": mathpix_key,
                "Content-type": "application/json"
            }
            data = {"src": f"data:image/jpeg;base64,{b64}", "formats": ["text", "latex_simplified"]}
            resp = requests.post("https://api.mathpix.com/v3/text", json=data, headers=headers, timeout=20)
            if resp.status_code == 200:
                j = resp.json()
                text = j.get("text", "")
                if not text:
                    # try other fields
                    text = j.get("data", {}).get("text", "")
                return text.strip()
        except Exception:
            pass

    try:
        pil = _preprocess_image(image_bytes)
        # Use rus+eng if possible
        try:
            text = pytesseract.image_to_string(pil, lang="rus+eng")
        except Exception:
            text = pytesseract.image_to_string(pil)
        return text.strip()
    except Exception:
        try:
            # fallback simple PIL
            pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            return pytesseract.image_to_string(pil).strip()
        except Exception:
            return ""
