"""
Examination notes per case and evidence.

Author: Mohit M
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Note:
    note_id: str
    case_id: str
    evidence_id: str | None
    author: str
    body: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: list[str] = field(default_factory=list)


class NotesStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / ".ai-ive" / "notes.json"
        self._notes: dict[str, list[Note]] = {}

    def _load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text())
            self._notes = {cid: [Note(**n) for n in items] for cid, items in raw.items()}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {cid: [asdict(n) for n in items] for cid, items in self._notes.items()}
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add(self, case_id: str, author: str, body: str, evidence_id: str | None = None, tags: list[str] | None = None) -> Note:
        self._load()
        note = Note(
            note_id=str(uuid.uuid4()),
            case_id=case_id,
            evidence_id=evidence_id,
            author=author,
            body=body,
            tags=tags or [],
        )
        self._notes.setdefault(case_id, []).append(note)
        self._save()
        return note

    def list(self, case_id: str) -> list[Note]:
        self._load()
        return self._notes.get(case_id, [])


notes_store = NotesStore()
