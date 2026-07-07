"""Forensic examination API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from aive.analysis.stream import StreamAnalyzer
from aive.api.examination_payload import examination_preview_fields, examination_preview_from_frame
from aive.api.examination_schemas import (
    ApplyFilterRequest,
    ExaminationPreviewResponse,
    RemoveFilterRequest,
    ResetRequest,
)
from aive.api.session import sessions
from aive.filters.engine import build_filter_chain, is_implemented
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


@router.post("/examination/apply-filter", response_model=ExaminationPreviewResponse)
def examination_apply_filter(body: ApplyFilterRequest) -> dict[str, Any]:
    """Apply a filter to the session pipeline (non-destructive; renders from master)."""
    try:
        session = sessions.apply_filter(body.session_id, body.filter_id, body.params, insert_at=body.insert_at)
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


@router.post("/examination/preview-filter", response_model=ExaminationPreviewResponse)
def examination_preview_filter(body: ApplyFilterRequest) -> dict[str, Any]:
    """Preview a filter on the master frame without committing to the pipeline."""
    session = sessions.get(body.session_id)
    if not session or session.master_frame is None:
        raise HTTPException(400, "No frame loaded — upload an image or load a video frame first")
    try:
        sessions.ensure_filter_allowed(body.filter_id, session.media_type)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    try:
        base_chain = list(session.filter_chain)
        for prefix in body.replace_filter_prefixes or []:
            base_chain = [(fid, params) for fid, params in base_chain if not fid.startswith(prefix)]
        chain = [(body.filter_id, body.params)] + base_chain
        preview_frame = build_filter_chain(chain).apply(session.master_frame.copy())
    except Exception as e:
        raise HTTPException(400, str(e)) from e
    return {
        **examination_preview_from_frame(session, preview_frame),
        "implemented": is_implemented(body.filter_id),
        "filter_id": body.filter_id,
    }


@router.post("/examination/reset", response_model=ExaminationPreviewResponse)
def examination_reset(body: ResetRequest) -> dict[str, Any]:
    """Clear the filter pipeline and restore the master frame."""
    try:
        session = sessions.reset_enhancement(body.session_id)
    except KeyError:
        raise HTTPException(404, "Session not found") from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return examination_preview_fields(session)


@router.get("/examination/preview", response_model=ExaminationPreviewResponse)
def examination_preview(session_id: str) -> dict[str, Any]:
    """Current session frame + pipeline — sync UI when returning to Examination Lab."""
    session = sessions.get(session_id)
    if not session or session.frame is None:
        raise HTTPException(400, "No frame loaded — upload an image or load a video frame first")
    return examination_preview_fields(session)


@router.post("/examination/remove-filter", response_model=ExaminationPreviewResponse)
def examination_remove_filter(body: RemoveFilterRequest) -> dict[str, Any]:
    """Remove one filter from the pipeline and re-render from master."""
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


class SecureMediaScanBody(BaseModel):
    root_path: str
    verify_manifest: bool = True


class SecureMediaLoadBody(BaseModel):
    root_path: str
    actor: str = "examiner"
    case_id: str | None = None


class SecureMediaBatchExportBody(BaseModel):
    source_root: str
    output_dir: str
    mode: str = "copy"  # copy | stream_copy
    report_dir: str | None = None
    preserve_structure: bool = True
    use_stream_copy: bool = True


class BrowseFolderBody(BaseModel):
    initial_dir: str | None = None
    title: str = "Select folder"


@router.post("/system/browse-folder")
def browse_folder(body: BrowseFolderBody) -> dict[str, Any]:
    """Open native folder picker on the local workstation (returns absolute path)."""
    from aive.system.folder_picker import pick_folder

    path = pick_folder(body.initial_dir)
    if not path:
        return {"success": False, "cancelled": True, "path": ""}
    return {"success": True, "cancelled": False, "path": path}


@router.post("/secure-media/scan")
def secure_media_scan(body: SecureMediaScanBody) -> dict[str, Any]:
    """R-145 — scan nested secure-media folder and hash all media files."""
    from aive.forensics.secure_media_batch import scan_secure_media

    root = Path(body.root_path).expanduser()
    return scan_secure_media(root, verify_manifest=body.verify_manifest)


@router.post("/secure-media/load")
def secure_media_load(body: SecureMediaLoadBody) -> dict[str, Any]:
    """R-145 — register secure-media files in the case (direct load, no copy)."""
    from aive.forensics.secure_media_batch import register_secure_media

    root = Path(body.root_path).expanduser()
    result = register_secure_media(root, actor=body.actor, case_id=body.case_id)
    if result.get("success"):
        case = case_store.active_case()
        audit_log.record(
            case.case_id,
            "SECURE_MEDIA_LOAD",
            body.actor,
            root=str(root),
            registered=result.get("registered", 0),
        )
    return result


@router.post("/secure-media/batch-export")
def secure_media_batch_export(body: SecureMediaBatchExportBody) -> dict[str, Any]:
    """R-145 — batch export from secure media with per-file hash reports."""
    from aive.forensics.secure_media_batch import batch_secure_export

    source = Path(body.source_root).expanduser()
    output = Path(body.output_dir).expanduser()
    report = Path(body.report_dir).expanduser() if body.report_dir else None
    result = batch_secure_export(
        source,
        output,
        mode=body.mode,
        report_dir=report,
        preserve_structure=body.preserve_structure,
        use_stream_copy=body.use_stream_copy,
    )
    case = case_store.active_case()
    audit_log.record(
        case.case_id,
        "SECURE_MEDIA_BATCH_EXPORT",
        case.examiner or "examiner",
        source=str(source),
        output=str(output),
        done=result.get("done", 0),
        failed=result.get("failed", 0),
    )
    return result
