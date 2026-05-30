"""
Live capture from devices and screen (OpenCV / FFmpeg).

Author: Mohit M
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aive.imaging import HAS_CV2

if HAS_CV2:
    import cv2


def list_capture_devices(max_index: int = 5) -> list[dict[str, Any]]:
    if not HAS_CV2:
        return []
    found = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            found.append({"index": i, "backend": "opencv"})
            cap.release()
    return found


def capture_frame(device_index: int = 0) -> dict[str, Any]:
    if not HAS_CV2:
        return {"success": False, "error": "OpenCV required"}
    cap = cv2.VideoCapture(device_index)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return {"success": False, "error": "Capture failed"}
    from aive.imaging import bgr_to_jpeg_base64

    return {"success": True, "preview": bgr_to_jpeg_base64(frame)}


def save_capture_sequence(device_index: int, output_dir: Path, count: int = 30) -> dict[str, Any]:
    if not HAS_CV2:
        return {"success": False, "error": "OpenCV required"}
    output_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(device_index)
    paths = []
    for i in range(count):
        ok, frame = cap.read()
        if not ok:
            break
        p = output_dir / f"seq_{i:05d}.jpg"
        cv2.imwrite(str(p), frame)
        paths.append(str(p))
    cap.release()
    return {"success": bool(paths), "frames": paths}
