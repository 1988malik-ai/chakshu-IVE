"""Project-linked examination notes API (R-195)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aive.forensics.audit import audit_log
from aive.project import examination_notes as project_notes
from aive.project.workflow import project_store

router = APIRouter(prefix="/api/project", tags=["project-notes"])


class ProjectNoteCreate(BaseModel):
    body: str
    author: str = "examiner"
    case_id: str | None = None
    evidence_id: str | None = None
    frame_index: int | None = None
    time_sec: float | None = None
    tags: list[str] = Field(default_factory=list)


class ProjectNoteUpdate(BaseModel):
    body: str | None = None
    tags: list[str] | None = None


@router.get("/notes")
def list_project_notes() -> dict[str, Any]:
    project_notes.hydrate_from_sidecar()
    proj = project_store.current
    notes = project_notes.list_notes()
    return {
        "project_id": proj.project_id,
        "project_name": proj.name,
        "notes": [n.to_dict() for n in notes],
        "count": len(notes),
    }


@router.post("/notes")
def create_project_note(body: ProjectNoteCreate) -> dict[str, Any]:
    if not body.body.strip():
        raise HTTPException(400, "Note body is required")
    note = project_notes.add_note(
        body.author,
        body.body,
        case_id=body.case_id,
        evidence_id=body.evidence_id,
        frame_index=body.frame_index,
        time_sec=body.time_sec,
        tags=body.tags,
    )
    audit_log.record(
        project_store.current.project_id,
        "PROJECT_NOTE_ADD",
        body.author,
        note_id=note.note_id,
    )
    project_store.current.add_step(
        "add_examination_note",
        settings={"note_id": note.note_id, "evidence_id": body.evidence_id},
        references=[note.note_id],
    )
    return {"note": note.to_dict(), "project_id": project_store.current.project_id}


@router.patch("/notes/{note_id}")
def patch_project_note(note_id: str, body: ProjectNoteUpdate) -> dict[str, Any]:
    try:
        note = project_notes.update_note(note_id, body.body, body.tags)
    except KeyError as e:
        raise HTTPException(404, str(e)) from e
    return {"note": note.to_dict()}


@router.delete("/notes/{note_id}")
def remove_project_note(note_id: str) -> dict[str, Any]:
    if not project_notes.delete_note(note_id):
        raise HTTPException(404, "Note not found")
    return {"success": True, "deleted": note_id}
