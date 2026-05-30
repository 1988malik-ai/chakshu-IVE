"""Extended API — export, reports, projects, audio."""

from __future__ import annotations

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
from aive.project.workflow import project_store
from aive.reports.generator import ReportSettings, generate_report

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
    include_original: bool = True
    include_processed: bool = True
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    use_stream_copy: bool = False
    frame_rate_mode: str = "cfr"
    fps: float | None = 29.97
    prefer_h265: bool = False


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
    title: str = "AI-IVE Processing Report"
    author: str = ""
    output_dir: str
    formats: list[str] = Field(default_factory=lambda: ["html", "pdf"])


class ProjectSaveRequest(BaseModel):
    name: str
    path: str | None = None


class ProjectImportRequest(BaseModel):
    path: str


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
    return result


@router.post("/export/media-bundle")
def api_media_bundle(body: MediaBundleRequest) -> dict[str, Any]:
    bundle = MediaExportBundle(
        input_path=expand_path(body.input_path),
        output_dir=expand_path(body.output_dir),
        include_original=body.include_original,
        include_processed=body.include_processed,
        video_codec=body.video_codec,
        audio_codec=body.audio_codec,
        use_stream_copy=body.use_stream_copy,
        frame_rate_mode=body.frame_rate_mode,
        fps=body.fps,
        prefer_h265=body.prefer_h265,
    )
    proc = expand_path(body.processed_path) if body.processed_path else None
    result = export_media_bundle(expand_path(body.input_path), proc, bundle)
    project_store.current.add_step("export_media_bundle", settings=body.model_dump())
    project_store.current.export_settings = body.model_dump()
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
    settings = ReportSettings(
        paper_size=body.paper_size,
        orientation=body.orientation,
        template=body.template,
        title=body.title,
        author=body.author,
        output_formats=body.formats,
    )
    result = generate_report(project_store.current, expand_path(body.output_dir), settings)
    project_store.current.add_step("generate_report", settings=body.model_dump())
    return result


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
    proj = project_store.import_compatible(p)
    return {
        "project_id": proj.project_id,
        "name": proj.name,
        "steps": len(proj.workflow_steps),
    }


@router.get("/project/current")
def api_project_current() -> dict[str, Any]:
    p = project_store.current
    return {
        "project_id": p.project_id,
        "name": p.name,
        "workflow_steps": [
            {"action": s.action, "timestamp": s.timestamp, "settings": s.settings}
            for s in p.workflow_steps
        ],
        "filter_pipeline": p.filter_pipeline,
    }


@router.get("/project/export-yaml")
def api_project_yaml() -> dict[str, str]:
    return {"yaml": project_store.current.to_yaml()}
