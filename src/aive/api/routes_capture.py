"""Phase 5 — capture, real-time preview, examples API."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from aive.api.session import sessions
from aive.capture.devices import list_capture_devices, save_capture_sequence
from aive.capture.realtime import get_live_session, stop_all_live_sessions
from aive.capture.screen import capture_screen
from aive.capture.sequence_video import images_to_video
from aive.examples.store import list_examples, load_example
from aive.imaging import HAS_CV2, bgr_from_bytes, bgr_to_jpeg_base64

router = APIRouter(prefix="/api/capture", tags=["capture"])


class SnapshotIngestBody(BaseModel):
    session_id: str
    preview_base64: str
    filename: str = "live-capture.jpg"


class ProcessFrameBody(BaseModel):
    filter_id: str
    preview_base64: str


class ScreenCaptureBody(BaseModel):
    output_path: str
    duration_sec: float = 5.0
    fps: float = 15.0


class SequenceVideoBody(BaseModel):
    input_dir: str
    output_path: str
    fps: float = 30.0
    pattern: str = "*.jpg"


class SequenceSaveBody(BaseModel):
    device_index: int = 0
    output_dir: str
    frame_count: int = 30


@router.get("/devices")
def capture_devices() -> dict[str, Any]:
    return {"devices": list_capture_devices(), "opencv": HAS_CV2}


@router.get("/stream/mjpeg")
async def mjpeg_stream(
    request: Request,
    device: int = Query(0),
    filter_id: str | None = Query(None),
    fps: float = Query(15.0, ge=1, le=30),
) -> StreamingResponse:
    if not HAS_CV2:
        raise HTTPException(503, "OpenCV required for device streaming")
    sess = get_live_session(device, filter_id)
    if not sess.open():
        raise HTTPException(503, f"Cannot open capture device {device}")

    async def generate():
        async for chunk in sess.async_mjpeg_stream(fps=fps, disconnected=request.is_disconnected):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache, no-store", "Connection": "keep-alive"},
    )


@router.post("/stream/stop")
def stop_stream(device: int | None = None) -> dict[str, str]:
    if device is not None:
        from aive.capture.realtime import release_device_sessions

        release_device_sessions(device)
    else:
        stop_all_live_sessions()
    return {"status": "stopped"}


@router.get("/snapshot")
def snapshot(device: int = 0, filter_id: str | None = None) -> dict[str, Any]:
    from aive.capture.realtime import release_device_sessions

    sess = get_live_session(device, filter_id)
    try:
        return sess.snapshot()
    finally:
        release_device_sessions(device)


@router.post("/process-frame")
def process_frame(body: ProcessFrameBody) -> dict[str, Any]:
    """Apply a catalog filter to a single JPEG frame (browser webcam live preview)."""
    if not body.filter_id:
        raise HTTPException(400, "filter_id required")
    raw = body.preview_base64
    if "," in raw:
        raw = raw.split(",", 1)[1]
    try:
        data = base64.b64decode(raw)
    except Exception as exc:
        raise HTTPException(400, f"Invalid base64: {exc}") from exc
    try:
        frame = bgr_from_bytes(data, "frame.jpg")
    except Exception as exc:
        raise HTTPException(400, f"Could not decode frame: {exc}") from exc
    from aive.filters.forensic_ops import apply_catalog_filter

    try:
        out = apply_catalog_filter(frame, body.filter_id, {})
    except Exception as exc:
        raise HTTPException(400, f"Filter failed: {exc}") from exc
    return {"preview": bgr_to_jpeg_base64(out), "filter_id": body.filter_id}


@router.post("/ingest")
def ingest_snapshot(body: SnapshotIngestBody) -> dict[str, Any]:
    raw = body.preview_base64
    if "," in raw:
        raw = raw.split(",", 1)[1]
    try:
        data = base64.b64decode(raw)
    except Exception as exc:
        raise HTTPException(400, f"Invalid base64: {exc}") from exc

    cap_dir = Path.home() / ".chakshu" / "captures"
    cap_dir.mkdir(parents=True, exist_ok=True)
    storage = cap_dir / body.filename
    storage.write_bytes(data)

    try:
        session = sessions.load_upload(body.session_id, data, body.filename, storage_path=str(storage))
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
    return {
        "session_id": body.session_id,
        "preview": sessions.frame_to_base64_jpeg(session.frame) if session.frame is not None else None,
        "media_type": session.media_type,
        "storage_path": str(storage),
        "source_path": str(storage),
    }


@router.post("/screen")
def screen_capture(body: ScreenCaptureBody) -> dict[str, Any]:
    return capture_screen(Path(body.output_path), body.duration_sec, body.fps)


@router.post("/sequence/save")
def save_sequence(body: SequenceSaveBody) -> dict[str, Any]:
    out = Path(body.output_dir).expanduser()
    return save_capture_sequence(body.device_index, out, body.frame_count)


@router.post("/sequence/to-video")
def sequence_to_video(body: SequenceVideoBody) -> dict[str, Any]:
    return images_to_video(body.input_dir, Path(body.output_path), body.fps, body.pattern)


@router.get("/examples")
def examples_list() -> dict[str, Any]:
    return {"examples": list_examples()}


@router.get("/examples/{example_id}")
def examples_get(example_id: str) -> dict[str, Any]:
    data = load_example(example_id)
    if data.get("error"):
        raise HTTPException(404, data["error"])
    return data
