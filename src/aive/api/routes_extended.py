"""Extended API — export, reports, projects, audio."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aive.api.paths import expand_path

from aive.api.session import sessions
from aive.export.audio import extract_audio, probe_audio_streams
from aive.export.i_frames import export_i_frames
from aive.export.media_bundle import MediaExportBundle, export_media_bundle
from aive.export.pdf_frames import PdfLayoutSettings, export_frames_to_pdf
from aive.project import examination_notes
from aive.bookmarks.store import BookmarkStore
from aive.forensics.case import case_store
from aive.project.workflow import inspect_compatible_project, project_store
from aive.reports.generator import ReportSettings, generate_report

_bookmark_store = BookmarkStore()

router = APIRouter(prefix="/api", tags=["extended"])


class PdfExportRequest(BaseModel):
    session_id: str
    output_path: str
    page_size: str = "A4"
    orientation: str = "portrait"
    columns: int = 2
    rows: int = 3
    margin_mm: float = 12.0
    title: str = "AI-IVE Frame Export"
    include_current_only: bool = True


class MediaBundleRequest(BaseModel):
    input_path: str
    processed_path: str | None = None
    output_dir: str
    original_dir: str | None = None
    processed_dir: str | None = None
    session_id: str | None = None
    include_original: bool = True
    include_processed: bool = True
    use_session_enhancement: bool = True
    video_codec: str = "auto_gpu"
    audio_codec: str = "aac"
    use_stream_copy: bool = False
    frame_rate_mode: str = "cfr"
    fps: float | None = 29.97
    prefer_h265: bool = False
    prefer_gpu: bool = True
    image_quality: int = 92
    crf: int | None = 23
    video_bitrate: str | None = None
    encode_preset: str = "medium"


class AudioExtractRequest(BaseModel):
    input_path: str
    output_path: str
    codec: str = "copy"


class IFrameExportRequest(BaseModel):
    input_path: str
    output_dir: str
    image_format: str = "jpg"


class ReportRequest(BaseModel):
    paper_size: str = "A4"
    orientation: str = "portrait"
    template: str = "standard"
    title: str = ""
    author: str = ""
    locale: str = "en"
    output_dir: str
    formats: list[str] = Field(default_factory=lambda: ["html", "pdf", "docx"])
    include_settings: bool = True
    include_references: bool = True
    include_notes: bool = True
    include_bookmarks: bool = True


class ProjectSaveRequest(BaseModel):
    name: str
    path: str | None = None


class ProjectImportRequest(BaseModel):
    path: str


class ProjectExportSettingsRequest(BaseModel):
    """Persist Legal Export paths and project folder structure on the active project."""

    project_root: str | None = None
    use_project_structure: bool | None = None
    folder_evidence: str | None = None
    folder_examination: str | None = None
    folder_bundles: str | None = None
    folder_pdf: str | None = None
    folder_reports: str | None = None
    folder_video_iframes: str | None = None
    folder_video_trim: str | None = None
    folder_audio: str | None = None
    folder_metadata: str | None = None
    folder_captures: str | None = None
    folder_subtitles: str | None = None
    output_dir: str | None = None
    evidence_dir: str | None = None
    examination_dir: str | None = None
    bundles_dir: str | None = None
    pdf_path: str | None = None
    i_frames_dir: str | None = None
    audio_out: str | None = None
    metadata_path: str | None = None
    input_path: str | None = None
    use_custom_paths: bool | None = None
    pdf_page_size: str | None = None
    pdf_orientation: str | None = None
    pdf_columns: int | None = None
    pdf_rows: int | None = None
    pdf_margin_mm: float | None = None
    pdf_title: str | None = None
    include_original: bool | None = None
    include_processed: bool | None = None
    use_session_enhancement: bool | None = None
    video_codec: str | None = None
    audio_codec: str | None = None
    use_stream_copy: bool | None = None
    frame_rate_mode: str | None = None
    fps: float | None = None
    prefer_h265: bool | None = None
    prefer_gpu: bool | None = None
    image_quality: int | None = None
    crf: int | None = None
    video_bitrate: str | None = None
    encode_preset: str | None = None


@router.post("/export/pdf-frames")
def api_pdf_frames(body: PdfExportRequest) -> dict[str, Any]:
    session = sessions.get(body.session_id)
    if not session or session.frame is None:
        raise HTTPException(404, "No frame in session")
    frames = [session.frame]
    layout = PdfLayoutSettings(
        page_size=body.page_size,
        orientation=body.orientation,
        columns=body.columns,
        rows=body.rows,
        margin_mm=body.margin_mm,
        title=body.title,
    )
    result = export_frames_to_pdf(frames, expand_path(body.output_path), layout)
    project_store.current.add_step("export_pdf_frames", settings=body.model_dump())
    es = project_store.current.export_settings or {}
    es.update(
        {
            "pdf_path": body.output_path,
            "pdf_page_size": body.page_size,
            "pdf_orientation": body.orientation,
            "pdf_columns": body.columns,
            "pdf_rows": body.rows,
            "pdf_margin_mm": body.margin_mm,
            "pdf_title": body.title,
        }
    )
    project_store.current.export_settings = es
    return result


@router.post("/export/media-bundle")
def api_media_bundle(body: MediaBundleRequest) -> dict[str, Any]:
    session = sessions.get(body.session_id) if body.session_id else None
    bundle = MediaExportBundle(
        input_path=expand_path(body.input_path),
        output_dir=expand_path(body.output_dir),
        original_dir=expand_path(body.original_dir) if body.original_dir else None,
        processed_dir=expand_path(body.processed_dir) if body.processed_dir else None,
        include_original=body.include_original,
        include_processed=body.include_processed,
        use_session_enhancement=body.use_session_enhancement,
        video_codec=body.video_codec,
        audio_codec=body.audio_codec,
        use_stream_copy=body.use_stream_copy,
        frame_rate_mode=body.frame_rate_mode,
        fps=body.fps,
        prefer_h265=body.prefer_h265,
        prefer_gpu=body.prefer_gpu,
        image_quality=body.image_quality,
        crf=body.crf,
        video_bitrate=body.video_bitrate,
        encode_preset=body.encode_preset,
    )
    proc = expand_path(body.processed_path) if body.processed_path else None
    result = export_media_bundle(expand_path(body.input_path), proc, bundle, session=session)
    project_store.current.add_step("export_media_bundle", settings=body.model_dump())
    es = project_store.current.export_settings or {}
    es.update(body.model_dump())
    project_store.current.export_settings = es
    return result


@router.post("/export/audio")
def api_extract_audio(body: AudioExtractRequest) -> dict[str, Any]:
    inp = expand_path(body.input_path)
    if not inp.exists():
        raise HTTPException(404, "Input not found")
    result = extract_audio(inp, expand_path(body.output_path), codec=body.codec)
    project_store.current.add_step("extract_audio", settings=body.model_dump())
    return result


@router.get("/audio/streams")
def api_audio_streams(path: str) -> dict[str, Any]:
    p = expand_path(path)
    if not p.exists():
        raise HTTPException(404, "File not found")
    return {"streams": probe_audio_streams(p)}


@router.post("/export/i-frames")
def api_i_frames(body: IFrameExportRequest) -> dict[str, Any]:
    inp = expand_path(body.input_path)
    if not inp.exists():
        raise HTTPException(404, "Input not found")
    result = export_i_frames(inp, expand_path(body.output_dir), image_format=body.image_format)
    project_store.current.add_step("export_i_frames", settings=body.model_dump())
    return result


@router.post("/reports/generate")
def api_generate_report(body: ReportRequest) -> dict[str, Any]:
    case = case_store.active_case()
    case_meta = {
        "case_id": case.case_id,
        "case_number": case.case_number,
        "display_id": case.display_id,
        "title": case.title,
        "examiner": case.examiner,
        "agency": case.agency,
    }
    settings = ReportSettings(
        paper_size=body.paper_size,
        orientation=body.orientation,
        template=body.template,
        title=body.title,
        author=body.author,
        locale=body.locale,
        output_formats=body.formats,
        include_settings=body.include_settings,
        include_references=body.include_references,
        include_notes=body.include_notes,
        include_bookmarks=body.include_bookmarks,
    )
    bookmarks = [_bookmark_store.to_dict(b) for b in _bookmark_store.all()]
    result = generate_report(
        project_store.current,
        expand_path(body.output_dir),
        settings,
        case_meta=case_meta,
        bookmarks=bookmarks,
    )
    project_store.current.add_step(
        "generate_report",
        settings=body.model_dump(),
        references=[o["path"] for o in result.get("outputs", [])],
    )
    return result


@router.get("/reports/preview")
def api_report_preview() -> dict[str, Any]:
    """Summary for UI before generating."""
    p = project_store.current
    return {
        "project_id": p.project_id,
        "project_name": p.name,
        "step_count": len(p.workflow_steps),
        "pipeline_count": len(p.filter_pipeline),
        "notes_count": len(p.examination_notes),
        "bookmark_count": len(_bookmark_store.all()),
        "recent_steps": [
            {
                "action": s.action,
                "timestamp": s.timestamp,
                "references": s.references,
                "settings_keys": list((s.settings or {}).keys()),
            }
            for s in p.workflow_steps[-8:]
        ],
    }


@router.get("/reports/templates")
def api_report_templates() -> dict[str, Any]:
    return {
        "templates": ["standard", "detailed", "executive", "minimal"],
        "paper_sizes": ["A4", "Letter", "Legal", "A3"],
        "orientations": ["portrait", "landscape"],
        "formats": ["html", "pdf", "docx"],
    }


@router.post("/project/new")
def api_project_new(body: ProjectSaveRequest) -> dict[str, Any]:
    proj = project_store.new_project(body.name)
    proj.examination_notes = []
    return {"project_id": proj.project_id, "name": proj.name}


@router.post("/project/save")
def api_project_save(body: ProjectSaveRequest) -> dict[str, Any]:
    if body.name:
        project_store.current.name = body.name
    path = project_store.save_current(expand_path(body.path) if body.path else None)
    return {"path": str(path), "project_id": project_store.current.project_id}


@router.post("/project/import")
def api_project_import(body: ProjectImportRequest) -> dict[str, Any]:
    p = expand_path(body.path)
    if not p.exists():
        raise HTTPException(404, "Project file not found")
    summary = inspect_compatible_project(p)
    if not summary.get("supported"):
        warnings = "; ".join(summary.get("warnings", []))
        raise HTTPException(400, f"Project format is not compatible. {warnings}".strip())
    proj = project_store.import_compatible(p)
    from aive.project import examination_notes as en

    en.hydrate_from_sidecar()
    return {
        "project_id": proj.project_id,
        "name": proj.name,
        "steps": len(proj.workflow_steps),
        "summary": summary,
    }


@router.post("/project/import/inspect")
def api_project_import_inspect(body: ProjectImportRequest) -> dict[str, Any]:
    p = expand_path(body.path)
    if not p.exists():
        raise HTTPException(404, "Project file not found")
    return inspect_compatible_project(p)


@router.get("/project/current")
def api_project_current() -> dict[str, Any]:
    examination_notes.hydrate_from_sidecar()
    p = project_store.current
    return {
        "project_id": p.project_id,
        "name": p.name,
        "workflow_steps": [
            {"action": s.action, "timestamp": s.timestamp, "settings": s.settings}
            for s in p.workflow_steps
        ],
        "filter_pipeline": p.filter_pipeline,
        "examination_notes_count": len(p.examination_notes),
        "export_settings": p.export_settings or {},
    }


@router.put("/project/export-settings")
def api_project_export_settings(body: ProjectExportSettingsRequest) -> dict[str, Any]:
    """Save Legal Export output paths to the active project (included in .aive.yaml on save)."""
    p = project_store.current
    patch = body.model_dump(exclude_none=True)
    p.export_settings = {**(p.export_settings or {}), **patch}
    p.updated = datetime.utcnow().isoformat()
    return {"export_settings": p.export_settings}


@router.get("/project/export-yaml")
def api_project_yaml() -> dict[str, str]:
    return {"yaml": project_store.current.to_yaml()}
