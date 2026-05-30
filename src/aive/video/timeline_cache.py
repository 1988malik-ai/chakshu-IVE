"""Persistent cache for forensic video timelines."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _file_key(path: Path) -> str:
    stat = path.stat()
    raw = f"{path.resolve()}|{stat.st_size}|{stat.st_mtime_ns}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


class TimelineCache:
    def __init__(self, base: Path | None = None) -> None:
        self.base = base or Path.home() / ".ai-ive" / "timeline-cache"
        self.base.mkdir(parents=True, exist_ok=True)

    def path_for(self, video: Path) -> Path:
        return self.base / f"{_file_key(video)}.json"

    def get(self, video: Path) -> dict[str, Any] | None:
        p = self.path_for(video)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    def put(self, video: Path, data: dict[str, Any]) -> None:
        p = self.path_for(video)
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def invalidate(self, video: Path) -> None:
        p = self.path_for(video)
        if p.exists():
            p.unlink()
