"""Bookmarks for frames and filters with customizable metadata."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Bookmark:
    id: str
    media_path: str
    bookmark_type: str  # frame | filter
    frame_index: int | None = None
    time_sec: float | None = None
    filter_id: str | None = None
    filter_params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    label: str = ""

    @staticmethod
    def new_frame(
        media_path: str,
        frame_index: int,
        time_sec: float,
        label: str = "",
        **metadata: Any,
    ) -> Bookmark:
        return Bookmark(
            id=str(uuid.uuid4()),
            media_path=media_path,
            bookmark_type="frame",
            frame_index=frame_index,
            time_sec=time_sec,
            label=label,
            metadata=metadata,
        )

    @staticmethod
    def new_filter(
        media_path: str,
        filter_id: str,
        filter_params: dict[str, Any] | None = None,
        frame_index: int | None = None,
        time_sec: float | None = None,
        label: str = "",
        **metadata: Any,
    ) -> Bookmark:
        return Bookmark(
            id=str(uuid.uuid4()),
            media_path=media_path,
            bookmark_type="filter",
            filter_id=filter_id,
            filter_params=filter_params or {},
            frame_index=frame_index,
            time_sec=time_sec,
            label=label,
            metadata=metadata,
        )


class BookmarkStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / ".ai-ive" / "bookmarks.json"
        self._items: list[Bookmark] = []
        self.load()

    def load(self) -> None:
        if self.path.exists():
            data = json.loads(self.path.read_text())
            self._items = [Bookmark(**b) for b in data.get("bookmarks", [])]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"bookmarks": [asdict(b) for b in self._items]}, indent=2)
        )

    def add(self, bookmark: Bookmark) -> Bookmark:
        self._items.append(bookmark)
        self.save()
        return bookmark

    def get(self, bookmark_id: str) -> Bookmark | None:
        for b in self._items:
            if b.id == bookmark_id:
                return b
        return None

    def remove(self, bookmark_id: str) -> bool:
        before = len(self._items)
        self._items = [b for b in self._items if b.id != bookmark_id]
        if len(self._items) < before:
            self.save()
            return True
        return False

    def update(
        self,
        bookmark_id: str,
        *,
        label: str | None = None,
        metadata: dict[str, Any] | None = None,
        frame_index: int | None = None,
        time_sec: float | None = None,
    ) -> Bookmark | None:
        bm = self.get(bookmark_id)
        if not bm:
            return None
        if label is not None:
            bm.label = label
        if metadata is not None:
            bm.metadata = metadata
        if frame_index is not None:
            bm.frame_index = frame_index
        if time_sec is not None:
            bm.time_sec = time_sec
        self.save()
        return bm

    def list_for_media(self, media_path: str) -> list[Bookmark]:
        return [b for b in self._items if b.media_path == media_path]

    def all(self) -> list[Bookmark]:
        return list(self._items)

    def to_dict(self, bookmark: Bookmark) -> dict[str, Any]:
        return {
            "id": bookmark.id,
            "media_path": bookmark.media_path,
            "type": bookmark.bookmark_type,
            "bookmark_type": bookmark.bookmark_type,
            "label": bookmark.label,
            "frame_index": bookmark.frame_index,
            "time_sec": bookmark.time_sec,
            "filter_id": bookmark.filter_id,
            "filter_params": bookmark.filter_params,
            "metadata": bookmark.metadata,
            "created": bookmark.created,
        }
