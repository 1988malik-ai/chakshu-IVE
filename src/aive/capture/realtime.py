"""
Live capture and real-time filtered preview (MJPEG).

Author: Mohit M
"""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Any, AsyncGenerator

from aive.imaging import HAS_CV2, bgr_to_jpeg_base64

if HAS_CV2:
    import cv2


class LiveCaptureSession:
    """Thread-safe OpenCV capture for MJPEG streaming."""

    def __init__(self, device_index: int = 0, filter_id: str | None = None) -> None:
        self.device_index = device_index
        self.filter_id = filter_id or None
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
            if self._cap.isOpened():
                self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return bool(self._cap and self._cap.isOpened())

    def close(self) -> None:
        with self._lock:
            self._running = False
            if self._cap:
                self._cap.release()
                self._cap = None

    def stop(self) -> None:
        self._running = False

    def _apply_live_filter(self, frame: Any) -> Any:
        if not self.filter_id:
            return frame
        from aive.filters.forensic_ops import apply_catalog_filter

        try:
            return apply_catalog_filter(frame, self.filter_id, {})
        except Exception:
            from aive.filters.engine import apply_filter

            try:
                return apply_filter(frame, self.filter_id, {})
            except Exception:
                return frame

    def read_frame(self) -> Any:
        if not self.open():
            return None
        with self._lock:
            if not self._cap:
                return None
            ok, frame = self._cap.read()
            if not ok or frame is None:
                return None
            return self._apply_live_filter(frame)

    def snapshot(self) -> dict[str, Any]:
        frame = self.read_frame()
        if frame is None:
            return {"success": False, "error": "Capture failed — check camera index and permissions"}
        return {
            "success": True,
            "preview": bgr_to_jpeg_base64(frame),
            "filter_id": self.filter_id,
        }

    def encode_jpeg_chunk(self, frame: Any) -> bytes | None:
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
        if not ok:
            return None
        chunk = buf.tobytes()
        return b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + chunk + b"\r\n"

    async def async_mjpeg_stream(
        self,
        fps: float = 15.0,
        disconnected: Any = None,
    ) -> AsyncGenerator[bytes, None]:
        """Async MJPEG generator with client disconnect cleanup."""
        self._running = True
        delay = 1.0 / max(fps, 1.0)
        try:
            while self._running:
                if disconnected is not None and await disconnected():
                    break
                frame = await asyncio.to_thread(self.read_frame)
                if frame is None:
                    await asyncio.sleep(delay)
                    continue
                chunk = await asyncio.to_thread(self.encode_jpeg_chunk, frame)
                if chunk:
                    yield chunk
                await asyncio.sleep(delay)
        finally:
            self.close()


_active_sessions: dict[str, LiveCaptureSession] = {}


def _session_key(device_index: int, filter_id: str | None) -> str:
    return f"live:{device_index}:{filter_id or ''}"


def release_device_sessions(device_index: int) -> None:
    """Release camera for device — required before switching filters on macOS/Windows."""
    prefix = f"live:{device_index}:"
    for key in list(_active_sessions):
        if key.startswith(prefix):
            _active_sessions[key].stop()
            _active_sessions[key].close()
            del _active_sessions[key]


def get_live_session(device_index: int, filter_id: str | None = None) -> LiveCaptureSession:
    release_device_sessions(device_index)
    key = _session_key(device_index, filter_id)
    sess = LiveCaptureSession(device_index, filter_id)
    _active_sessions[key] = sess
    return sess


def stop_all_live_sessions() -> None:
    for sess in list(_active_sessions.values()):
        sess.stop()
        sess.close()
    _active_sessions.clear()


def stop_live_session(session_key: str) -> None:
    for key in list(_active_sessions):
        if key.startswith(session_key):
            _active_sessions[key].stop()
            _active_sessions[key].close()
            del _active_sessions[key]
