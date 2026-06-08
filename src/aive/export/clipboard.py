"""R-134 — clipboard-friendly export payloads."""

from __future__ import annotations

import base64
from typing import Any

import numpy as np

from aive.forensics.hash_verify import hash_frame


def frame_clipboard_payload(frame: np.ndarray, include_hash: bool = True) -> dict[str, Any]:
    from aive.imaging import bgr_to_jpeg_base64

    b64 = bgr_to_jpeg_base64(frame, quality=90)
    payload: dict[str, Any] = {
        "format": "image/jpeg",
        "base64": b64,
        "data_url": f"data:image/jpeg;base64,{b64}",
        "width": int(frame.shape[1]),
        "height": int(frame.shape[0]),
        "clipboard_hint": "Use data_url in browser or decode base64 for file paste",
    }
    if include_hash:
        payload["hashes"] = hash_frame(frame)
    return payload


def text_clipboard_payload(text: str) -> dict[str, Any]:
    return {"text": text, "length": len(text)}
