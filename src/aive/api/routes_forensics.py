"""Forensic examination API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aive.analysis.stream import StreamAnalyzer
from aive.api.examination_payload import examination_preview_fields
from aive.api.session import sessions
from aive.filters.engine import is_implemented
from aive.filters.forensic import FORENSIC_FILTER_IDS
from aive.forensics.audit import audit_log
from aive.forensics.case import case_store
from aive.project.workflow import project_store

router = APIRouter(prefix="/api/forensics", tags=["forensics"])
_analyzer = StreamAnalyzer()


class CreateCaseRequest(BaseModel):
    case_number: str = ""
    title: str = "New Examination"
    examiner: str = "Examiner"
    agency: str = ""


def _case_summary(c) -> dict[str, Any]:
    return {
        "case_id": c.case_id,
        "case_number": c.case_number,
        "display_id": c.display_id,
        "title": c.title,
        "examiner": c.examiner,
        "agency": c.agency,
        "status": c.status,
        "created": c.created,
    }


class IngestRequest(BaseModel):
    case_id: str | None = None
    session_id: str
    actor: str = "examiner"
    filename: str


class ApplyFilterRequest(BaseModel):
    session_id: str
    filter_id: str
    params: dict[str, Any] | None = None
    actor: str = "examiner"


class FrameAtTimeRequest(BaseModel):
    session_id: str
    path: str
    time_sec: float


@router.get("/filters/implemented")
def list_implemented() -> dict[str, Any]:
    return {"count": len(FORENSIC_FILTER_IDS), "ids": sorted(FORENSIC_FILTER_IDS)}


@router.get("/cases")
def list_cases() -> dict[str, Any]:
    cases = case_store.list_cases()
    return {
        "cases": [
            {
                **_case_summary(c),
                "evidence_count": len(c.evidence),
            }
            for c in cases
        ]
    }


@router.post("/cases")
def create_case(body: CreateCaseRequest) -> dict[str, Any]:
    c = case_store.create_case(body.case_number, body.title, body.examiner, body.agency)
    audit_log.record(c.case_id, "CASE_CREATE", body.examiner, case_number=body.case_number)
    return {**_case_summary(c), "evidence_count": len(c.evidence)}


@router.get("/cases/active")
def active_case() -> dict[str, Any]:
    c = case_store.active_case()
    return {
        **_case_summary(c),
        "evidence": [
            {
                "evidence_id": e.evidence_id,
                "filename": e.filename,
                "sha256": e.sha256,
                "size_bytes": e.size_bytes,
                "media_type": e.media_type,
                "storage_path": e.storage_path,
            }
            for e in c.evidence
        ],
    }


@router.get("/cases/{case_id}/custody")
def custody_log(case_id: str) -> dict[str, Any]:
    case_store._load_all()
    case = case_store._cases.get(case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    log = []
    for ev in case.evidence:
        for c in ev.custody:
            log.append({
                "evidence_id": ev.evidence_id,
                "filename": ev.filename,
                "sha256": ev.sha256,
                **{
                    "timestamp": c.timestamp,
                    "action": c.action,
                    "actor": c.actor,
                    "notes": c.notes,
                },
            })
    log.sort(key=lambda x: x["timestamp"])
    return {"entries": log}


@router.get("/cases/{case_id}/audit")
def case_audit(case_id: str) -> dict[str, Any]:
    events = audit_log.list_for_case(case_id)
    return {"events": [e.__dict__ for e in events]}


@router.post("/evidence/register")
def register_evidence(body: IngestRequest, data: bytes = None) -> dict[str, Any]:
    raise HTTPException(400, "Use /evidence/ingest multipart endpoint")


@router.post("/examination/apply-filter")
def examination_apply_filter(body: ApplyFilterRequest) -> dict[str, Any]:
    try:
        session = sessions.apply_filter(body.session_id, body.filter_id, body.params)
    except KeyError:
        raise HTTPException(404, "Session not found") from None
    except Exception as e:
        raise HTTPException(400, str(e)) from e

    case = case_store.active_case()
    if session.evidence_id:
        case.log_custody(
            session.evidence_id,
            "ENHANCE",
            body.actor,
            notes=f"filter={body.filter_id}",
        )
    audit_log.record(case.case_id, "FILTER_APPLY", body.actor, filter_id=body.filter_id)
    project_store.current.add_step(
        "forensic_enhance",
        settings={"filter_id": body.filter_id, "params": body.params},
        references=[body.filter_id],
    )
    project_store.current.filter_pipeline.append({"filter_id": body.filter_id, "params": body.params})

    return {
        **examination_preview_fields(session),
        "implemented": is_implemented(body.filter_id),
        "can_undo": session.undo.can_undo,
    }


class ResetRequest(BaseModel):
    session_id: str


@router.post("/examination/reset")
def examination_reset(body: ResetRequest) -> dict[str, Any]:
    session = sessions.reset_enhancement(body.session_id)
    return examination_preview_fields(session)


@router.get("/examination/preview")
def examination_preview(session_id: str) -> dict[str, Any]:
    """Current session frame + pipeline — sync UI when returning to Examination Lab."""
    session = sessions.get(session_id)
    if not session or session.frame is None:
        raise HTTPException(400, "No frame loaded in session")
    return examination_preview_fields(session)


class RemoveFilterRequest(BaseModel):
    session_id: str
    index: int
    actor: str = "examiner"


@router.post("/examination/remove-filter")
def examination_remove_filter(body: RemoveFilterRequest) -> dict[str, Any]:
    pre = sessions.get(body.session_id)
    if pre is None:
        raise HTTPException(404, "Session not found")
    if body.index < 0 or body.index >= len(pre.filter_chain):
        raise HTTPException(400, f"Filter index out of range: {body.index}")

    removed_id = pre.filter_chain[body.index][0]
    try:
        session = sessions.remove_filter_at(body.session_id, body.index)
    except Exception as e:
        raise HTTPException(400, str(e)) from e

    pipeline = project_store.current.filter_pipeline
    if 0 <= body.index < len(pipeline):
        pipeline.pop(body.index)
    project_store.current.add_step(
        "remove_filter",
        settings={"index": body.index, "filter_id": removed_id},
        references=[removed_id],
    )

    case = case_store.active_case()
    audit_log.record(
        case.case_id,
        "FILTER_REMOVE",
        body.actor,
        index=body.index,
        filter_id=removed_id,
        filter_chain=[f[0] for f in session.filter_chain],
    )

    return {
        **examination_preview_fields(session),
        "removed_index": body.index,
        "removed_filter_id": removed_id,
        "can_undo": session.undo.can_undo,
    }


@router.post("/examination/analyze-video")
def analyze_video(path: str) -> dict[str, Any]:
    p = Path(path).expanduser()
    if not p.exists():
        raise HTTPException(404, "Not found")
    summary = _analyzer.frame_type_summary(p)
    streams = _analyzer.probe_streams(p)
    frames = _analyzer.extract_timestamps(p)[:500]
    return {"summary": summary, "streams": streams, "frame_sample_count": len(frames)}


@router.get("/examination/hash")
def file_hash(path: str, algorithm: str = "all") -> dict[str, Any]:
    from aive.forensics.hash_verify import hash_all_algorithms, hash_file

    p = Path(path).expanduser()
    if not p.exists():
        raise HTTPException(404, "Not found")
    if algorithm == "all":
        return {"path": str(p), "hashes": hash_all_algorithms(p)}
    return {"path": str(p), "hash": hash_file(p, algorithm), "algorithm": algorithm}
