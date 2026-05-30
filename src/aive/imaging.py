"""Image I/O with OpenCV when available, Pillow otherwise."""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Any

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

try:
    import cv2

    HAS_CV2 = True
except ImportError:
    cv2 = None  # type: ignore
    HAS_CV2 = False


def bgr_from_bytes(data: bytes, filename: str = "") -> np.ndarray:
    if HAS_CV2:
        arr = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is not None:
            return frame

    try:
        pil = Image.open(BytesIO(data))
        if pil.mode in ("RGBA", "LA", "P"):
            pil = pil.convert("RGB")
        elif pil.mode != "RGB":
            pil = pil.convert("RGB")
        rgb = np.array(pil)
        return rgb[:, :, ::-1].copy()  # RGB → BGR for pipeline compatibility
    except Exception as e:
        raise ValueError(f"Could not decode image '{filename}': {e}") from e


def bgr_to_jpeg_base64(frame: np.ndarray, quality: int = 85) -> str:
    if HAS_CV2:
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if ok:
            return base64.b64encode(buf.tobytes()).decode("ascii")

    rgb = frame[:, :, ::-1]
    img = Image.fromarray(rgb.astype(np.uint8))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def apply_basic_filter(frame: np.ndarray, filter_id: str, params: dict[str, Any]) -> np.ndarray:
    """Pillow-based filters when OpenCV is not installed."""
    rgb = frame[:, :, ::-1]
    img = Image.fromarray(rgb.astype(np.uint8))

    if filter_id in ("clr_grayscale",):
        img = img.convert("L").convert("RGB")
    elif filter_id in ("clr_invert",):
        from PIL import ImageOps

        img = ImageOps.invert(img.convert("RGB"))
    elif filter_id.startswith("clr_brightness") or filter_id == "both_normalize":
        amount = float(params.get("amount", params.get("stops", 0)))
        factor = 2.0**amount if "stops" in params or filter_id == "both_normalize" else 1.0 + amount
        img = ImageEnhance.Brightness(img).enhance(factor)
    elif filter_id.startswith("clr_contrast") or filter_id == "both_auto_contrast":
        amount = float(params.get("amount", 1.0))
        img = ImageEnhance.Contrast(img).enhance(amount)
    elif filter_id.startswith("clr_saturation"):
        amount = float(params.get("amount", 1.0))
        img = ImageEnhance.Color(img).enhance(amount)
    elif filter_id.startswith("clr_gamma"):
        gamma = float(params.get("gamma", 1.0))
        inv = 1.0 / max(gamma, 0.01)
        lut = [int(((i / 255.0) ** inv) * 255) for i in range(256)]
        img = img.point(lut * 3)
    elif filter_id.startswith("clr_sharpness") or filter_id.startswith("shp_") or filter_id.startswith("both_sharpen"):
        img = img.filter(ImageFilter.SHARPEN)
    elif filter_id.startswith("blr_gaussian") or filter_id.startswith("both_blur"):
        radius = max(1, int(float(params.get("radius", 3))))
        img = img.filter(ImageFilter.GaussianBlur(radius=radius))
    elif filter_id.startswith("blr_box"):
        radius = max(1, int(float(params.get("radius", 3))))
        img = img.filter(ImageFilter.BoxBlur(radius))
    elif filter_id.startswith("sty_emboss"):
        img = img.filter(ImageFilter.EMBOSS)
    elif filter_id.startswith("sty_edge_detect") or filter_id.startswith("sty_canny"):
        img = img.filter(ImageFilter.FIND_EDGES)
    elif filter_id.startswith("clr_sepia") or filter_id.startswith("clr_film_emulation"):
        from PIL import ImageOps

        img = ImageOps.colorize(img.convert("L"), "#2e1f0f", "#f4e2c8")
    elif filter_id.startswith("sty_vignette") or filter_id.startswith("both_vignette"):
        from PIL import ImageDraw

        w, h = img.size
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((-w // 4, -h // 4, w + w // 4, h + h // 4), fill=255)
        mask = ImageEnhance.Brightness(mask).enhance(float(params.get("amount", 0.5)))
        dark = Image.new("RGB", (w, h), (0, 0, 0))
        img = Image.composite(img, dark, mask)
    elif filter_id.startswith(("utl_", "vid_", "geo_", "ns_", "rst_", "key_", "both_", "frn_")):
        # Best-effort Pillow pass-through enhancement for Phase 4 catalog
        img = ImageEnhance.Contrast(ImageEnhance.Brightness(img).enhance(1.05)).enhance(1.08)
    else:
        return frame.copy()

    out = np.array(img.convert("RGB"))
    return out[:, :, ::-1].copy()
