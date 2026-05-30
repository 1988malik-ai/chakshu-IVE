"""
Forensic annotations — arrows, text, shapes with optional tracking.

Author: Mohit M
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from aive.annotations.snap import snap_point
from aive.imaging import HAS_CV2

if HAS_CV2:
    import cv2


@dataclass
class Annotation:
    id: str
    type: str  # arrow | text | rect | ellipse | line
    frame_index: int
    time_sec: float
    points: list[list[float]]
    text: str = ""
    color: tuple[int, int, int] = (0, 255, 255)
    thickness: int = 2
    group_id: str | None = None
    tracked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class AnnotationStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / ".ai-ive" / "annotations.json"
        self._items: dict[str, list[Annotation]] = {}

    def load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text())
            for media_id, items in raw.items():
                parsed = []
                for a in items:
                    if isinstance(a.get("color"), list):
                        a["color"] = tuple(a["color"][:3])
                    parsed.append(Annotation(**a))
                self._items[media_id] = parsed

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {mid: [asdict(a) for a in items] for mid, items in self._items.items()}
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add(self, media_id: str, ann: Annotation) -> Annotation:
        self._items.setdefault(media_id, []).append(ann)
        self.save()
        return ann

    def list(self, media_id: str) -> list[Annotation]:
        return self._items.get(media_id, [])

    def delete(self, media_id: str, annotation_id: str) -> bool:
        self.load()
        items = self._items.get(media_id, [])
        new_items = [a for a in items if a.id != annotation_id]
        if len(new_items) == len(items):
            return False
        self._items[media_id] = new_items
        self.save()
        return True

    def list_groups(self, media_id: str) -> list[str]:
        groups = {a.group_id for a in self.list(media_id) if a.group_id}
        return sorted(groups)

    def render_on_frame(self, frame: np.ndarray, media_id: str, frame_index: int) -> np.ndarray:
        if not HAS_CV2:
            return frame
        out = frame.copy()
        for ann in self.list(media_id):
            if ann.frame_index != frame_index:
                continue
            color = ann.color
            pts = ann.points
            if ann.type == "arrow" and len(pts) >= 2:
                p1 = (int(pts[0][0]), int(pts[0][1]))
                p2 = (int(pts[1][0]), int(pts[1][1]))
                cv2.arrowedLine(out, p1, p2, color, ann.thickness)
            elif ann.type == "rect" and len(pts) >= 2:
                cv2.rectangle(out, (int(pts[0][0]), int(pts[0][1])), (int(pts[1][0]), int(pts[1][1])), color, ann.thickness)
            elif ann.type == "text" and pts:
                cv2.putText(out, ann.text, (int(pts[0][0]), int(pts[0][1])), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            elif ann.type == "ellipse" and len(pts) >= 2:
                center = (int((pts[0][0] + pts[1][0]) / 2), int((pts[0][1] + pts[1][1]) / 2))
                axes = (int(abs(pts[1][0] - pts[0][0]) / 2), int(abs(pts[1][1] - pts[0][1]) / 2))
                cv2.ellipse(out, center, axes, 0, 0, 360, color, ann.thickness)
            elif ann.type == "line" and len(pts) >= 2:
                cv2.line(out, (int(pts[0][0]), int(pts[0][1])), (int(pts[1][0]), int(pts[1][1])), color, ann.thickness)
            elif ann.type == "measure" and len(pts) >= 2:
                cv2.line(out, (int(pts[0][0]), int(pts[0][1])), (int(pts[1][0]), int(pts[1][1])), (255, 200, 0), 2)
                label = ann.text or ann.metadata.get("distance_label", "")
                if label:
                    cv2.putText(out, label, (int(pts[0][0]), int(pts[0][1]) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1)
        return out


annotation_store = AnnotationStore()


def snap_points(points: list[list[float]], width: int, height: int, grid: int = 10) -> list[list[float]]:
    return [list(snap_point(p[0], p[1], width, height, grid=grid)) for p in points]
