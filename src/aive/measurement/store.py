"""Persist measurement results per examination."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class MeasurementRecord:
    id: str
    media_id: str
    frame_index: int
    p1: list[float]
    p2: list[float]
    result: dict[str, Any]
    label: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class MeasurementStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / ".ai-ive" / "measurements.json"
        self._data: dict[str, list[MeasurementRecord]] = {}

    def _load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text())
            self._data = {
                mid: [MeasurementRecord(**m) for m in items]
                for mid, items in raw.items()
            }

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {mid: [asdict(m) for m in items] for mid, items in self._data.items()}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add(self, media_id: str, frame_index: int, p1: list[float], p2: list[float], result: dict[str, Any], label: str = "") -> MeasurementRecord:
        self._load()
        rec = MeasurementRecord(
            id=str(uuid.uuid4()),
            media_id=media_id,
            frame_index=frame_index,
            p1=p1,
            p2=p2,
            result=result,
            label=label,
        )
        self._data.setdefault(media_id, []).append(rec)
        self._save()
        return rec

    def list(self, media_id: str) -> list[MeasurementRecord]:
        self._load()
        return self._data.get(media_id, [])


measurement_store = MeasurementStore()
