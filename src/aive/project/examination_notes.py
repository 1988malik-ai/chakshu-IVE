"""Examination notes persisted on the active AiveProject (R-195)."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from aive.project.workflow import project_store


@dataclass
class ExaminationNote:
    note_id: str
    author: str
    body: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    case_id: str | None = None
    evidence_id: str | None = None
    frame_index: int | None = None
    time_sec: float | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ExaminationNote:
        return cls(
            note_id=str(raw.get("note_id", uuid.uuid4())),
            author=str(raw.get("author", "examiner")),
            body=str(raw.get("body", "")),
            timestamp=str(raw.get("timestamp", datetime.utcnow().isoformat())),
            case_id=raw.get("case_id"),
            evidence_id=raw.get("evidence_id"),
            frame_index=raw.get("frame_index"),
            time_sec=raw.get("time_sec"),
            tags=list(raw.get("tags") or []),
        )


def _touch_project() -> None:
    project_store.current.updated = datetime.utcnow().isoformat()


def list_notes() -> list[ExaminationNote]:
    return [ExaminationNote.from_dict(n) for n in project_store.current.examination_notes]


def add_note(
    author: str,
    body: str,
    *,
    case_id: str | None = None,
    evidence_id: str | None = None,
    frame_index: int | None = None,
    time_sec: float | None = None,
    tags: list[str] | None = None,
) -> ExaminationNote:
    note = ExaminationNote(
        note_id=str(uuid.uuid4()),
        author=author or "examiner",
        body=body.strip(),
        case_id=case_id,
        evidence_id=evidence_id,
        frame_index=frame_index,
        time_sec=time_sec,
        tags=tags or [],
    )
    project_store.current.examination_notes.append(note.to_dict())
    _touch_project()
    _autosave_sidecar()
    return note


def update_note(note_id: str, body: str | None = None, tags: list[str] | None = None) -> ExaminationNote:
    for raw in project_store.current.examination_notes:
        if raw.get("note_id") == note_id:
            if body is not None:
                raw["body"] = body.strip()
            if tags is not None:
                raw["tags"] = tags
            raw["timestamp"] = datetime.utcnow().isoformat()
            _touch_project()
            _autosave_sidecar()
            return ExaminationNote.from_dict(raw)
    raise KeyError(f"Note not found: {note_id}")


def delete_note(note_id: str) -> bool:
    notes = project_store.current.examination_notes
    for i, raw in enumerate(notes):
        if raw.get("note_id") == note_id:
            notes.pop(i)
            _touch_project()
            _autosave_sidecar()
            return True
    return False


def _autosave_sidecar() -> None:
    """Write notes immediately so they survive without explicit project save."""
    try:
        path = project_store.base_dir / f"{project_store.current.project_id}_notes.json"
        import json

        path.write_text(
            json.dumps(project_store.current.examination_notes, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def hydrate_from_sidecar() -> None:
    """Restore notes if project YAML had none but sidecar exists."""
    import json

    path = project_store.base_dir / f"{project_store.current.project_id}_notes.json"
    if project_store.current.examination_notes or not path.exists():
        return
    try:
        project_store.current.examination_notes = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
