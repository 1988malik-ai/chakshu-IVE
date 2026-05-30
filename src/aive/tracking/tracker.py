"""Object tracking — manual, automatic, keyframe-based with reusable data."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import cv2
import numpy as np


class TrackingMode(str, Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    KEYFRAME = "keyframe"


@dataclass
class TrackPoint:
    frame_index: int
    x: float
    y: float
    width: float
    height: float
    confidence: float = 1.0


@dataclass
class TrackingSession:
    id: str
    media_path: str
    mode: TrackingMode
    object_label: str = ""
    points: list[TrackPoint] = field(default_factory=list)
    keyframes: dict[int, tuple[float, float, float, float]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "media_path": self.media_path,
            "mode": self.mode.value,
            "object_label": self.object_label,
            "points": [asdict(p) for p in self.points],
            "keyframes": {str(k): v for k, v in self.keyframes.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TrackingSession:
        return cls(
            id=data["id"],
            media_path=data["media_path"],
            mode=TrackingMode(data["mode"]),
            object_label=data.get("object_label", ""),
            points=[TrackPoint(**p) for p in data.get("points", [])],
            keyframes={int(k): tuple(v) for k, v in data.get("keyframes", {}).items()},
        )


class ObjectTracker:
    """OpenCV-based tracking with export/import of tracking data."""

    def __init__(self) -> None:
        self._sessions: dict[str, TrackingSession] = {}
        self._cv_tracker = None

    def create_session(
        self, session_id: str, media_path: str, mode: TrackingMode, label: str = ""
    ) -> TrackingSession:
        session = TrackingSession(id=session_id, media_path=media_path, mode=mode, object_label=label)
        self._sessions[session_id] = session
        return session

    def add_manual_point(
        self, session_id: str, frame_index: int, bbox: tuple[float, float, float, float]
    ) -> None:
        session = self._sessions[session_id]
        x, y, w, h = bbox
        session.points.append(TrackPoint(frame_index, x, y, w, h))

    def add_keyframe(
        self, session_id: str, frame_index: int, bbox: tuple[float, float, float, float]
    ) -> None:
        session = self._sessions[session_id]
        session.keyframes[frame_index] = bbox
        session.mode = TrackingMode.KEYFRAME

    def track_automatic(
        self,
        frames: list[np.ndarray],
        init_bbox: tuple[int, int, int, int],
        session_id: str,
        tracker_type: str = "CSRT",
    ) -> list[TrackPoint]:
        session = self._sessions[session_id]
        session.mode = TrackingMode.AUTOMATIC
        tracker_ctor = getattr(cv2, f"Tracker{tracker_type}_create", None) or getattr(
            cv2.legacy, "TrackerCSRT_create", None
        )
        if tracker_ctor is None:
            tracker_ctor = cv2.TrackerKCF_create  # type: ignore
        tracker = tracker_ctor()
        points = []
        for i, frame in enumerate(frames):
            if i == 0:
                tracker.init(frame, init_bbox)
                x, y, w, h = init_bbox
                points.append(TrackPoint(0, float(x), float(y), float(w), float(h)))
            else:
                ok, box = tracker.update(frame)
                if ok:
                    x, y, w, h = box
                    points.append(TrackPoint(i, float(x), float(y), float(w), float(h)))
        session.points.extend(points)
        return points

    def interpolate_keyframes(self, session_id: str, total_frames: int) -> list[TrackPoint]:
        session = self._sessions[session_id]
        if not session.keyframes:
            return []
        keys = sorted(session.keyframes.items())
        points = []
        for frame_idx in range(total_frames):
            prev = next((k for k in keys if k[0] <= frame_idx), None)
            nxt = next((k for k in keys if k[0] >= frame_idx), None)
            if prev and nxt and prev[0] != nxt[0]:
                t = (frame_idx - prev[0]) / (nxt[0] - prev[0])
                bbox = tuple(prev[1][j] + t * (nxt[1][j] - prev[1][j]) for j in range(4))
            elif prev:
                bbox = prev[1]
            elif nxt:
                bbox = nxt[1]
            else:
                continue
            points.append(TrackPoint(frame_idx, bbox[0], bbox[1], bbox[2], bbox[3]))
        session.points = points
        return points

    def save(self, path: Path) -> None:
        data = {sid: s.to_dict() for sid, s in self._sessions.items()}
        path.write_text(json.dumps(data, indent=2))

    def load(self, path: Path) -> None:
        data = json.loads(path.read_text())
        self._sessions = {sid: TrackingSession.from_dict(d) for sid, d in data.items()}

    def get_session(self, session_id: str) -> TrackingSession | None:
        return self._sessions.get(session_id)
