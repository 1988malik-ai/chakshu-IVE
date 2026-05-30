"""
Live capture and real-time filtered preview (MJPEG).

Author: Mohit M
"""

from __future__ import annotations

import threading
import time
from typing import Any, Generator

from aive.imaging import HAS_CV2, bgr_to_jpeg_base64

if HAS_CV2:
    import cv2


class LiveCaptureSession:
    """Thread-safe OpenCV capture for MJPEG streaming."""

    def __init__(self, device_index: int = 0, filter_id: str | None = None) -> None:
        self.device_index = device_index
        self.filter_id = filter_id
        self._cap: Any = None
        self._lock = threading.Lock()
        self._running = False

    def open(self) -> bool:
        if not HAS_CV2:
            return False
        with self._lock:
            if self._cap and self._cap.isOpened():
                return True
            self._cap = cv2.VideoCapture(self.device_index)
            return bool(self._cap.isOpened())

    def close(self) -> None:
        with self._lock:
            self._running = False
            if self._cap:
                self._cap.release()
                self._cap = None

    def read_frame(self) -> Any:
        if not self.open():
            return None
        with self._lock:
            if not self._cap:
                return None
            ok, frame = self._cap.read()
            if not ok:
                return None
            if self.filter_id:
                from aive.filters.engine import apply_filter

                try:
                    frame = apply_filter(frame, self.filter_id)
                except Exception:
                    pass
            return frame

    def snapshot(self) -> dict[str, Any]:
        frame = self.read_frame()
        if frame is None:
            return {"success": False, "error": "Capture failed"}
        return {"success": True, "preview": bgr_to_jpeg_base64(frame)}

    def mjpeg_stream(self, fps: float = 15.0) -> Generator[bytes, None, None]:
        self._running = True
        delay = 1.0 / max(fps, 1.0)
        while self._running:
            frame = self.read_frame()
            if frame is None:
                time.sleep(delay)
                continue
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
            if not ok:
                continue
            chunk = buf.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + chunk + b"\r\n"
            )
            time.sleep(delay)
        self.close()


_active_sessions: dict[str, LiveCaptureSession] = {}


def get_live_session(session_key: str, device_index: int = 0, filter_id: str | None = None) -> LiveCaptureSession:
    key = f"{session_key}:{device_index}:{filter_id or ''}"
    if key not in _active_sessions:
        _active_sessions[key] = LiveCaptureSession(device_index, filter_id)
    else:
        sess = _active_sessions[key]
        sess.filter_id = filter_id
    return _active_sessions[key]


def stop_live_session(session_key: str) -> None:
    for k, sess in list(_active_sessions.items()):
        if k.startswith(session_key):
            sess.close()
            del _active_sessions[k]
