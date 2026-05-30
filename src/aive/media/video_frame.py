"""Extract video frames via FFmpeg or OpenCV."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from aive.codecs.decoders import get_decoder
from aive.imaging import HAS_CV2, bgr_from_bytes

if HAS_CV2:
    import cv2

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".mxf", ".ts", ".m4v", ".mpg", ".mpeg",
}


def is_video_filename(name: str) -> bool:
    return Path(name).suffix.lower() in VIDEO_EXTENSIONS


def extract_frame_bgr(path: Path, time_sec: float = 0.0) -> np.ndarray | None:
    path = path.expanduser().resolve()
    if not path.exists():
        return None

    if HAS_CV2:
        cap = cv2.VideoCapture(str(path))
        if cap.isOpened():
            if time_sec > 0:
                cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000)
            else:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
            cap.release()
            if ok and frame is not None:
                return frame

    decoder = get_decoder("ffmpeg")
    raw = decoder.extract_frame(path, time_sec)
    if raw:
        try:
            return bgr_from_bytes(raw, "frame.png")
        except ValueError:
            pass
    return None
