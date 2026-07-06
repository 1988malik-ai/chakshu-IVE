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


def draw_grid(
    frame: np.ndarray,
    step: int = 50,
    *,
    style: str = "uniform",
    divisions: int | None = None,
) -> np.ndarray:
    """Draw measurement grid on frame (R-123). style: uniform | thirds | center."""
    if not HAS_CV2:
        return frame
    out = frame.copy()
    h, w = out.shape[:2]
    minor = (80, 80, 80)
    major = (0, 200, 190)

    if style == "thirds":
        for x in (w // 3, (2 * w) // 3):
            cv2.line(out, (x, 0), (x, h), major, 2)
        for y in (h // 3, (2 * h) // 3):
            cv2.line(out, (0, y), (w, y), major, 2)
        return out

    if style == "center":
        cv2.line(out, (w // 2, 0), (w // 2, h), major, 2)
        cv2.line(out, (0, h // 2), (w, h // 2), major, 2)
        return out

    if divisions and divisions > 1:
        step_x = max(1, w // divisions)
        step_y = max(1, h // divisions)
        for i, x in enumerate(range(0, w, step_x)):
            color = major if i > 0 and i % 4 == 0 else minor
            thickness = 2 if color == major else 1
            cv2.line(out, (x, 0), (x, h), color, thickness)
        for i, y in enumerate(range(0, h, step_y)):
            color = major if i > 0 and i % 4 == 0 else minor
            thickness = 2 if color == major else 1
            cv2.line(out, (0, y), (w, y), color, thickness)
        return out

    for x in range(0, w, max(1, step)):
        cv2.line(out, (x, 0), (x, h), minor, 1)
    for y in range(0, h, max(1, step)):
        cv2.line(out, (0, y), (w, y), minor, 1)
    return out


def draw_pip(
    background: np.ndarray,
    inset: np.ndarray,
    scale: float = 0.25,
    position: str = "top-right",
    margin: int = 10,
) -> np.ndarray:
    if not HAS_CV2:
        return background
    out = background.copy()
    h, w = out.shape[:2]
    ih, iw = inset.shape[:2]
    nw, nh = max(32, int(iw * scale)), max(24, int(ih * scale))
    small = cv2.resize(inset, (nw, nh))
    positions = {
        "top-left": (margin, margin),
        "top-right": (w - nw - margin, margin),
        "bottom-left": (margin, h - nh - margin),
        "bottom-right": (w - nw - margin, h - nh - margin),
    }
    x0, y0 = positions.get(position, positions["top-right"])
    x1, y1 = x0 + nw, y0 + nh
    cv2.rectangle(out, (x0 - 2, y0 - 2), (x1 + 2, y1 + 2), (0, 0, 0), 2)
    out[y0:y1, x0:x1] = small
    return out


def draw_subtitle_cue(
    frame: np.ndarray,
    text: str,
    *,
    position: str = "bottom-center",
    font_scale: float | None = None,
    margin_v: int = 28,
) -> np.ndarray:
    """Render subtitle text on a video frame (R-120 preview / examination overlay)."""
    if not HAS_CV2 or not text:
        return frame
    out = frame.copy()
    h, w = out.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = font_scale if font_scale is not None else max(0.45, w / 1600)
    thickness = max(1, int(scale * 2))
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        return out
    max_tw = 0
    th = 0
    for ln in lines:
        (tw, th_line), _ = cv2.getTextSize(ln, font, scale, thickness)
        max_tw = max(max_tw, tw)
        th = max(th, th_line)
    line_h = int(th * 1.35)
    block_h = line_h * len(lines) + 8
    y_base = h - margin_v if "bottom" in position else margin_v + block_h
    x_center = w // 2
    x0 = max(4, x_center - max_tw // 2 - 8)
    y0 = max(4, y_base - block_h)
    x1 = min(w - 4, x_center + max_tw // 2 + 8)
    y1 = min(h - 4, y_base + 4)
    cv2.rectangle(out, (x0, y0), (x1, y1), (0, 0, 0), -1)
    cv2.rectangle(out, (x0, y0), (x1, y1), (200, 200, 200), 1)
    for i, ln in enumerate(lines):
        (tw, th), _ = cv2.getTextSize(ln, font, scale, thickness)
        x = x_center - tw // 2
        y = y0 + 8 + th + i * line_h
        cv2.putText(out, ln, (x, y), font, scale, (255, 255, 255), thickness)
    return out


def side_by_side(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    if not HAS_CV2:
        return left
    h = max(left.shape[0], right.shape[0])
    left_r = cv2.resize(left, (left.shape[1], h))
    right_r = cv2.resize(right, (right.shape[1], h))
    return np.hstack([left_r, right_r])
