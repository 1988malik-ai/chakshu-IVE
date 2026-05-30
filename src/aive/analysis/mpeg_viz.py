"""
MPEG macroblock / motion vector visualization (simplified).

Author: Mohit M
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from aive.imaging import HAS_CV2, bgr_from_bytes, bgr_to_jpeg_base64

if HAS_CV2:
    import cv2


def macroblock_grid_overlay(frame: np.ndarray, block_size: int = 16) -> np.ndarray:
    if not HAS_CV2:
        return frame
    out = frame.copy()
    h, w = out.shape[:2]
    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            cv2.rectangle(out, (x, y), (min(x + block_size, w), min(y + block_size, h)), (0, 255, 0), 1)
    return out


def motion_field_stub(frame: np.ndarray, step: int = 32) -> np.ndarray:
    """Placeholder motion vectors from local gradient direction."""
    if not HAS_CV2:
        return frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    out = frame.copy()
    h, w = gray.shape
    for y in range(step, h - step, step):
        for x in range(step, w - step, step):
            patch = gray[y - 4 : y + 4, x - 4 : x + 4].astype(np.float32)
            gx = patch[:, 2:].mean() - patch[:, :-2].mean()
            gy = patch[2:, :].mean() - patch[:-2, :].mean()
            mag = max(1.0, (gx * gx + gy * gy) ** 0.5)
            dx, dy = int(gx / mag * 8), int(gy / mag * 8)
            cv2.arrowedLine(out, (x, y), (x + dx, y + dy), (255, 128, 0), 1, tipLength=0.3)
    return out


def visualize_frame(path: Path, time_sec: float, mode: str = "macroblock") -> dict[str, Any]:
    import base64 as b64

    from aive.imaging import bgr_from_bytes
    from aive.video.seek import extract_frame_at_time

    base = extract_frame_at_time(path, time_sec)
    if not base.get("success"):
        return base
    raw = b64.b64decode(base["preview"])
    frame = bgr_from_bytes(raw, "frame.jpg")
    if mode == "motion":
        vis = motion_field_stub(frame)
    else:
        vis = macroblock_grid_overlay(frame)
    return {"success": True, "mode": mode, "preview": bgr_to_jpeg_base64(vis)}
