"""
Privacy redaction — pixelation and blur regions.

Author: Mohit M
"""

from __future__ import annotations

from typing import Any

import numpy as np

from aive.imaging import HAS_CV2

if HAS_CV2:
    import cv2


def redact_region(
    frame: np.ndarray,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    mode: str = "pixelate",
    block_size: int = 16,
) -> np.ndarray:
    if not HAS_CV2:
        return frame
    out = frame.copy()
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)
    roi = out[y1:y2, x1:x2]
    if roi.size == 0:
        return out
    if mode == "blur":
        roi[:] = cv2.GaussianBlur(roi, (31, 31), 0)
    else:
        h, w = roi.shape[:2]
        small = cv2.resize(roi, (max(1, w // block_size), max(1, h // block_size)), interpolation=cv2.INTER_LINEAR)
        roi[:] = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    return out


def redact_regions(frame: np.ndarray, regions: list[dict[str, Any]]) -> np.ndarray:
    out = frame
    for r in regions:
        out = redact_region(
            out,
            int(r["x1"]),
            int(r["y1"]),
            int(r["x2"]),
            int(r["y2"]),
            mode=r.get("mode", "pixelate"),
            block_size=int(r.get("block_size", 16)),
        )
    return out
