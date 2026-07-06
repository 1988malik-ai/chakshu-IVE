"""
Side-by-side and dual-source comparison sessions.

Author: Mohit M
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from aive.imaging import HAS_CV2, bgr_from_bytes, bgr_to_jpeg_base64
from aive.media.video_frame import extract_frame_bgr, is_video_filename
from aive.overlays.compose import draw_pip, side_by_side
from aive.video.seek import extract_frame_at_time

if HAS_CV2:
    import cv2


@dataclass
class CompareSession:
    id: str
    left_path: str
    right_path: str
    left_time: float = 0.0
    right_time: float = 0.0


def _frame_bgr(path: Path, time_sec: float) -> np.ndarray | None:
    if is_video_filename(path.name):
        result = extract_frame_at_time(path, time_sec)
        if not result.get("success") or not result.get("preview"):
            frame = extract_frame_bgr(path, time_sec)
            return frame
        import base64 as b64

        return bgr_from_bytes(b64.b64decode(result["preview"]), path.name)
    if HAS_CV2:
        frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if frame is not None:
            return frame
    return bgr_from_bytes(path.read_bytes(), path.name)


class CompareStore:
    def __init__(self) -> None:
        self._sessions: dict[str, CompareSession] = {}

    def create(self, left: Path, right: Path) -> CompareSession:
        s = CompareSession(id=str(uuid.uuid4()), left_path=str(left), right_path=str(right))
        self._sessions[s.id] = s
        return s

    def get(self, session_id: str) -> CompareSession | None:
        return self._sessions.get(session_id)

    def render(
        self,
        session_id: str,
        *,
        mode: str = "side_by_side",
        pip_scale: float = 0.28,
        pip_position: str = "top-right",
    ) -> dict[str, Any]:
        s = self._sessions.get(session_id)
        if not s:
            return {"success": False, "error": "Session not found"}
        left_path = Path(s.left_path)
        right_path = Path(s.right_path)
        lf = _frame_bgr(left_path, s.left_time)
        rf = _frame_bgr(right_path, s.right_time)
        if lf is None or rf is None:
            return {"success": False, "error": "Could not load one or both sources"}
        if mode == "pip":
            combined = draw_pip(lf, rf, scale=pip_scale, position=pip_position)
        else:
            combined = side_by_side(lf, rf)
        return {
            "success": True,
            "preview": bgr_to_jpeg_base64(combined),
            "left_time": s.left_time,
            "right_time": s.right_time,
            "left_path": s.left_path,
            "right_path": s.right_path,
            "mode": mode,
            "width": int(combined.shape[1]),
            "height": int(combined.shape[0]),
        }


compare_store = CompareStore()
