"""FastAPI backend for React frontend."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from aive.analysis.stream import StreamAnalyzer
from aive.api.session import sessions
from aive.bookmarks.store import Bookmark, BookmarkStore
from aive.export.exporter import ExportOptions, FrameRateMode, VideoExporter
from aive.filters.catalog import filter_count, list_filters
from aive.gpu.encode import detect_available_encoders, select_encoder
from aive.i18n.translations import LOCALES, Translator
from aive.license.protection import activate_license, check_license, machine_fingerprint
from aive.api.config import cors_origins, get_api_host, get_api_port
from aive.subtitles.renderer import SubtitleParser
from aive.api.routes_extended import router as extended_router
from aive.api.routes_forensics import router as forensics_router
from aive.api.routes_capabilities import router as capabilities_router
from aive.api.routes_timeline import router as timeline_router
from aive.api.routes_markup import router as markup_router
from aive.api.routes_capture import router as capture_router
from aive.brand import PRODUCT_NAME, API_TITLE
from aive.filters.engine import is_implemented
from aive.project.workflow import project_store
from aive.forensics.case import case_store
from aive.forensics.audit import audit_log
from aive.media.loader import MediaLibrary
from aive.media.video_frame import is_video_filename

app = FastAPI(title=API_TITLE, version="1.0.0")
app.include_router(extended_router)
app.include_router(forensics_router)
app.include_router(capabilities_router)
app.include_router(timeline_router)
app.include_router(markup_router)
app.include_router(capture_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bookmarks = BookmarkStore()
_analyzer = StreamAnalyzer()
_exporter = VideoExporter()


# --- Schemas ---


class SessionCreateResponse(BaseModel):
    session_id: str


class FilterApplyRequest(BaseModel):
    session_id: str
    filter_id: str
    params: dict[str, Any] | None = None


class FilterRemoveRequest(BaseModel):
    session_id: str
    index: int


class SessionRequest(BaseModel):
    session_id: str


class LoadPathRequest(BaseModel):
    session_id: str
    path: str


class LicenseActivateRequest(BaseModel):
    license_key: str


class ExportRequest(BaseModel):
    input_path: str
    output_path: str
    use_stream_copy: bool = True
    frame_rate_mode: str = "cfr"
    fps: float | None = 29.97
    prefer_h265: bool = False


class BookmarkCreateRequest(BaseModel):
    media_path: str
    bookmark_type: str = "frame"
    frame_index: int | None = 0
    time_sec: float | None = 0.0
    filter_id: str | None = None
    label: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


# --- Routes ---


@app.get("/api/health")
def health() -> dict[str, Any]:
    from aive.codecs.ffmpeg_bin import media_tools_status
    from aive.imaging import HAS_CV2

    media = media_tools_status()
    return {
        "status": "ok",
        "app": PRODUCT_NAME,
        "product": PRODUCT_NAME,
        "opencv": HAS_CV2,
        "ffmpeg": media["ffmpeg"],
        "ffprobe": media["ffprobe"],
        "ffmpeg_path": media.get("ffmpeg_path"),
        "ffmpeg_source": media.get("source"),
    }


@app.post("/api/session", response_model=SessionCreateResponse)
def create_session() -> SessionCreateResponse:
    s = sessions.create()
    return SessionCreateResponse(session_id=s.id)


@app.get("/api/filters")
def get_filters() -> dict[str, Any]:
    items = [
        {
            "id": f.id,
            "name": f.name,
            "category": f.category.value,
            "domain": f.domain.value,
            "description": f.description,
        }
        for f in list_filters()
    ]
    for it in items:
        it["implemented"] = is_implemented(it["id"])
    return {"count": filter_count(), "filters": items, "implemented_count": sum(1 for i in items if i["implemented"])}


@app.post("/api/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    session_id: str = Query(default=""),
    session_id_form: str = Form(default="", alias="session_id"),
) -> dict[str, Any]:
    sid = session_id or session_id_form
    if not sid:
        raise HTTPException(400, "session_id is required")

    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")

    filename = file.filename or "upload.bin"
    library = MediaLibrary()
    media_type = library.classify(Path(filename)).value
    if media_type == "unknown":
        media_type = "image" if not is_video_filename(filename) else "video"

    storage_path: str | None = None
    try:
        case = case_store.active_case()
        ev = case_store.add_evidence_from_bytes(
            case.case_id, data, filename, media_type, "system"
        )
        storage_path = ev.storage_path
        audit_log.record(case.case_id, "EVIDENCE_INGEST", "system", filename=filename, sha256=ev.sha256)
    except Exception:
        pass

    if not storage_path:
        upload_dir = Path.home() / ".ai-ive" / "uploads" / sid
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest = upload_dir / Path(filename).name
        dest.write_bytes(data)
        storage_path = str(dest)

    try:
        session = sessions.load_upload(sid, data, filename, storage_path=storage_path)
    except Exception as e:
        raise HTTPException(400, str(e)) from e

    if session.evidence_id is None:
        try:
            case = case_store.active_case()
            for ev in case.evidence:
                if ev.storage_path == storage_path:
                    session.evidence_id = ev.evidence_id
                    break
        except Exception:
            pass

    project_store.current.add_step(
        "load_media",
        settings={"filename": filename, "storage_path": storage_path},
        references=[filename],
    )
    project_store.current.media.append({"filename": filename, "type": media_type, "path": storage_path})

    if session.frame is None:
        raise HTTPException(400, "Failed to decode media (install ffmpeg for video)")

    try:
        preview = sessions.frame_to_base64_jpeg(session.frame)
    except Exception as e:
        raise HTTPException(500, f"Preview encoding failed: {e}") from e

    return {
        "session_id": session.id,
        "filename": filename,
        "storage_path": storage_path,
        "source_path": session.source_path,
        "media_type": session.media_type,
        "metadata": session.metadata,
        "preview": preview,
        "width": int(session.frame.shape[1]),
        "height": int(session.frame.shape[0]),
        "can_undo": session.undo.can_undo,
        "can_redo": session.undo.can_redo,
        "evidence_id": session.evidence_id,
    }


@app.get("/api/media/serve")
def serve_media(path: str) -> Any:
    """Stream evidence file for HTML5 video player (local forensic workstation only)."""
    from fastapi.responses import FileResponse

    p = Path(path).expanduser().resolve()
    allowed_roots = [
        (Path.home() / ".ai-ive").resolve(),
        (Path.home() / ".chakshu").resolve(),
    ]
    if not any(str(p).startswith(str(root)) for root in allowed_roots):
        raise HTTPException(403, "Path not allowed")
    if not p.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(p, filename=p.name)


@app.post("/api/media/load-path")
def load_path(body: LoadPathRequest) -> dict[str, Any]:
    """Load file by absolute path (desktop/Electron shell)."""
    if not Path(body.path).exists():
        raise HTTPException(404, f"File not found: {body.path}")
    try:
        session = sessions.load_path(body.session_id, body.path)
    except Exception as e:
        raise HTTPException(400, str(e)) from e
    preview = None
    if session.frame is not None:
        preview = sessions.frame_to_base64_jpeg(session.frame)
    return {
        "session_id": session.id,
        "path": body.path,
        "storage_path": body.path,
        "source_path": session.source_path,
        "media_type": session.media_type,
        "metadata": session.metadata,
        "preview": preview,
        "can_undo": session.undo.can_undo,
        "can_redo": session.undo.can_redo,
    }


class SeekVideoRequest(BaseModel):
    session_id: str
    time_sec: float


@app.post("/api/media/seek")
def seek_video(body: SeekVideoRequest) -> dict[str, Any]:
    try:
        session = sessions.seek_video(body.session_id, body.time_sec)
    except KeyError:
        raise HTTPException(404, "Session not found") from None
    except Exception as e:
        raise HTTPException(400, str(e)) from e
    return {
        "preview": sessions.frame_to_base64_jpeg(session.frame),
        "time_sec": session.time_sec,
        "frame_index": session.frame_index,
        "filter_chain": [f[0] for f in session.filter_chain],
        "can_undo": session.undo.can_undo,
    }


@app.get("/api/media/preview/{session_id}")
def get_preview(session_id: str) -> dict[str, Any]:
    session = sessions.get(session_id)
    if not session or session.frame is None:
        raise HTTPException(404, "No preview available")
    return {
        "preview": sessions.frame_to_base64_jpeg(session.frame),
        "can_undo": session.undo.can_undo,
        "can_redo": session.undo.can_redo,
        "filter_chain": [f[0] for f in session.filter_chain],
    }


@app.post("/api/filters/apply")
def apply_filter(body: FilterApplyRequest) -> dict[str, Any]:
    try:
        session = sessions.apply_filter(body.session_id, body.filter_id, body.params)
    except KeyError:
        raise HTTPException(404, "Session not found") from None
    except Exception as e:
        raise HTTPException(400, str(e)) from e
    project_store.current.filter_pipeline.append(
        {"filter_id": body.filter_id, "params": body.params or {}}
    )
    project_store.current.add_step(
        "apply_filter",
        settings={"filter_id": body.filter_id, "params": body.params},
        references=[body.filter_id],
    )
    return {
        "preview": sessions.frame_to_base64_jpeg(session.frame),
        "can_undo": session.undo.can_undo,
        "can_redo": session.undo.can_redo,
        "filter_chain": [f[0] for f in session.filter_chain],
    }


@app.post("/api/filters/remove")
def remove_filter(body: FilterRemoveRequest) -> dict[str, Any]:
    try:
        session = sessions.remove_filter_at(body.session_id, body.index)
    except KeyError:
        raise HTTPException(404, "Session not found") from None
    except IndexError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(400, str(e)) from e
    return {
        "preview": sessions.frame_to_base64_jpeg(session.frame),
        "can_undo": session.undo.can_undo,
        "can_redo": session.undo.can_redo,
        "filter_chain": [f[0] for f in session.filter_chain],
        "removed_index": body.index,
    }


@app.post("/api/edit/undo")
def undo(body: SessionRequest) -> dict[str, Any]:
    try:
        session = sessions.undo(body.session_id)
    except KeyError:
        raise HTTPException(404, "Session not found") from None
    if session.frame is None:
        raise HTTPException(400, "No frame")
    return {
        "preview": sessions.frame_to_base64_jpeg(session.frame),
        "can_undo": session.undo.can_undo,
        "can_redo": session.undo.can_redo,
    }


@app.post("/api/edit/redo")
def redo(body: SessionRequest) -> dict[str, Any]:
    try:
        session = sessions.redo(body.session_id)
    except KeyError:
        raise HTTPException(404, "Session not found") from None
    if session.frame is None:
        raise HTTPException(400, "No frame")
    return {
        "preview": sessions.frame_to_base64_jpeg(session.frame),
        "can_undo": session.undo.can_undo,
        "can_redo": session.undo.can_redo,
    }


@app.get("/api/license/status")
def license_status() -> dict[str, Any]:
    s = check_license()
    return {
        "valid": s.valid,
        "message": s.message,
        "licensed_to": s.licensed_to,
        "is_trial": s.is_trial,
        "days_remaining": s.days_remaining,
        "machine_id": machine_fingerprint(),
    }


@app.post("/api/license/activate")
def license_activate(body: LicenseActivateRequest) -> dict[str, Any]:
    s = activate_license(body.license_key.strip())
    return {"valid": s.valid, "message": s.message, "licensed_to": s.licensed_to}


@app.get("/api/gpu/encoders")
def gpu_encoders() -> dict[str, Any]:
    enc = detect_available_encoders()
    codec, vendor = select_encoder()
    return {
        "available": [{"name": e.name, "h264": e.codec_h264, "h265": e.codec_h265} for e in enc],
        "selected": {"codec": codec, "vendor": vendor.value},
    }


@app.post("/api/analysis/frame-types")
def frame_types(body: LoadPathRequest) -> dict[str, Any]:
    p = Path(body.path)
    if not p.exists():
        raise HTTPException(404, "File not found")
    summary = _analyzer.frame_type_summary(p)
    streams = _analyzer.probe_streams(p)
    return {
        "summary": summary,
        "streams": [
            {
                "codec": s.codec,
                "width": s.width,
                "height": s.height,
                "fps": s.fps,
                "duration": s.duration,
            }
            for s in streams
        ],
    }


@app.get("/api/bookmarks")
def get_bookmarks(media_path: str | None = None) -> dict[str, Any]:
    items = _bookmarks.all()
    if media_path:
        items = _bookmarks.list_for_media(media_path)
    return {
        "bookmarks": [
            {
                "id": b.id,
                "media_path": b.media_path,
                "type": b.bookmark_type,
                "label": b.label,
                "frame_index": b.frame_index,
                "time_sec": b.time_sec,
                "filter_id": b.filter_id,
                "metadata": b.metadata,
            }
            for b in items
        ]
    }


@app.post("/api/bookmarks")
def add_bookmark(body: BookmarkCreateRequest) -> dict[str, Any]:
    if body.bookmark_type == "filter" and body.filter_id:
        bm = Bookmark.new_filter(
            body.media_path,
            body.filter_id,
            frame_index=body.frame_index,
            label=body.label,
            **body.metadata,
        )
    else:
        bm = Bookmark.new_frame(
            body.media_path,
            body.frame_index or 0,
            body.time_sec or 0.0,
            label=body.label,
            **body.metadata,
        )
    _bookmarks.add(bm)
    return {"id": bm.id, "label": bm.label}


@app.post("/api/export")
def export_video(body: ExportRequest) -> dict[str, Any]:
    inp = Path(body.input_path)
    if not inp.exists():
        raise HTTPException(404, "Input not found")
    codec, _ = select_encoder(prefer_h265=body.prefer_h265)
    gpu = codec if any(x in codec for x in ("nvenc", "qsv", "amf")) else None
    opts = ExportOptions(
        output_path=Path(body.output_path),
        video_codec=codec,
        gpu_encoder=gpu,
        use_stream_copy=body.use_stream_copy,
        frame_rate_mode=FrameRateMode(body.frame_rate_mode),
        fps=body.fps,
    )
    return _exporter.export(inp, opts)


@app.get("/api/i18n/{locale}")
def i18n_strings(locale: str) -> dict[str, Any]:
    if locale not in LOCALES:
        locale = "en"
    tr = Translator(locale)
    keys = [
        "app.title",
        "menu.file",
        "menu.edit",
        "action.open",
        "action.export",
        "action.undo",
        "action.redo",
        "filter.browser",
    ]
    return {"locale": locale, "strings": {k: tr.tr(k) for k in keys}}


@app.post("/api/subtitles/parse")
def parse_subtitles(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise HTTPException(404, "File not found")
    cues = SubtitleParser.load(p)
    return {"count": len(cues), "cues": [{"start": c.start_sec, "end": c.end_sec, "text": c.text} for c in cues[:100]]}


def mount_frontend(dist_dir: Path) -> None:
    if dist_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")


def run(
    host: str | None = None,
    port: int | None = None,
    frontend_dist: str | None = None,
) -> None:
    import uvicorn

    host = host or get_api_host()
    port = port if port is not None else get_api_port()

    if frontend_dist:
        mount_frontend(Path(frontend_dist))
    elif env_dist := os.environ.get("AIVE_FRONTEND_DIST"):
        mount_frontend(Path(env_dist))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()
