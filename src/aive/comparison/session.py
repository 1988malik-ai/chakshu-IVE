"""
Side-by-side and dual-source comparison sessions.

Author: Mohit M
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from aive.imaging import HAS_CV2
from aive.overlays.compose import side_by_side
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


class CompareStore:
    def __init__(self) -> None:
        self._sessions: dict[str, CompareSession] = {}

    def create(self, left: Path, right: Path) -> CompareSession:
        s = CompareSession(id=str(uuid.uuid4()), left_path=str(left), right_path=str(right))
        self._sessions[s.id] = s
        return s

    def render(self, session_id: str) -> dict[str, Any]:
        s = self._sessions.get(session_id)
        if not s:
            return {"success": False, "error": "Session not found"}
        left = extract_frame_at_time(Path(s.left_path), s.left_time)
        right = extract_frame_at_time(Path(s.right_path), s.right_time)
        if not left.get("success") or not right.get("success"):
            return {"success": False, "error": "Frame extract failed"}
        import base64 as b64

        from aive.imaging import bgr_from_bytes, bgr_to_jpeg_base64

        lf = bgr_from_bytes(b64.b64decode(left["preview"]), "l.jpg")
        rf = bgr_from_bytes(b64.b64decode(right["preview"]), "r.jpg")
        combined = side_by_side(lf, rf)
        return {
            "success": True,
            "preview": bgr_to_jpeg_base64(combined),
            "left_time": s.left_time,
            "right_time": s.right_time,
        }


compare_store = CompareStore()
