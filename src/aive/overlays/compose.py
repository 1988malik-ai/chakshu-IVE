"""
Video/image overlays — timestamp, grid, subtitles on frame.

Author: Mohit M
"""

from __future__ import annotations

from typing import Any

import numpy as np

from aive.imaging import HAS_CV2

if HAS_CV2:
    import cv2


def draw_timestamp(frame: np.ndarray, text: str, position: str = "bottom-right") -> np.ndarray:
    if not HAS_CV2:
        return frame
    out = frame.copy()
    h, w = out.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = max(0.4, w / 1920)
    thickness = max(1, int(scale * 2))
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    margin = 10
    positions = {
        "top-left": (margin, margin + th),
        "top-right": (w - tw - margin, margin + th),
        "bottom-left": (margin, h - margin),
        "bottom-right": (w - tw - margin, h - margin),
    }
    xy = positions.get(position, positions["bottom-right"])
    cv2.rectangle(out, (xy[0] - 4, xy[1] - th - 4), (xy[0] + tw + 4, xy[1] + 4), (0, 0, 0), -1)
    cv2.putText(out, text, xy, font, scale, (255, 255, 255), thickness)
    return out


def draw_grid(frame: np.ndarray, step: int = 50) -> np.ndarray:
    if not HAS_CV2:
        return frame
    out = frame.copy()
    h, w = out.shape[:2]
    for x in range(0, w, step):
        cv2.line(out, (x, 0), (x, h), (80, 80, 80), 1)
    for y in range(0, h, step):
        cv2.line(out, (0, y), (w, y), (80, 80, 80), 1)
    return out


def draw_pip(background: np.ndarray, inset: np.ndarray, scale: float = 0.25) -> np.ndarray:
    if not HAS_CV2:
        return background
    out = background.copy()
    h, w = out.shape[:2]
    ih, iw = inset.shape[:2]
    nw, nh = int(iw * scale), int(ih * scale)
    small = cv2.resize(inset, (nw, nh))
    out[10 : 10 + nh, w - nw - 10 : w - 10] = small
    return out


def side_by_side(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    if not HAS_CV2:
        return left
    h = max(left.shape[0], right.shape[0])
    left_r = cv2.resize(left, (left.shape[1], h))
    right_r = cv2.resize(right, (right.shape[1], h))
    return np.hstack([left_r, right_r])
