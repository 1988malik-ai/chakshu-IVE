"""Phase 2 — video timeline, frame step, synced A/V, multi-video."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aive.analysis.frame_metadata import analyze_file, region_summary
from aive.api.session import sessions
from aive.audio.player import audio_time_for_frame, extract_audio_clip, probe_multichannel, stream_sync_offset
from aive.media.loader import MediaLibrary
from aive.video.timeline import build_timeline, filter_timeline, frame_at_step, nearest_iframe

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


def _path(p: str) -> Path:
    path = Path(p).expanduser()
    if not path.exists():
        raise HTTPException(404, f"Not found: {p}")
    return path


class PathQuery(BaseModel):
    path: str
    limit: int = 25000
    force_refresh: bool = False


class FilterBody(BaseModel):
    path: str
    types: list[str] = Field(default_factory=list)
    key_frames_only: bool = False
    start_sec: float | None = None
    end_sec: float | None = None
    limit: int = 2000


class RegionBody(BaseModel):
    path: str
    start_sec: float
    end_sec: float
    limit: int = 5000


class StepFrameBody(BaseModel):
    session_id: str
    delta: int = 1
    use_iframe: bool = False


class SecondaryVideoBody(BaseModel):
    session_id: str
    path: str
    label: str = "secondary"


class AudioSyncBody(BaseModel):
    path: str
    frame_index: int = 0
    fps: float | None = None
    pts_sec: float | None = None


@router.post("/build")
def timeline_build(body: PathQuery) -> dict[str, Any]:
    return build_timeline(_path(body.path), limit=body.limit, force_refresh=body.force_refresh)


@router.post("/filter")
def timeline_filter(body: FilterBody) -> dict[str, Any]:
    return filter_timeline(
        _path(body.path),
        types=body.types or None,
        key_frames_only=body.key_frames_only,
        start_sec=body.start_sec,
        end_sec=body.end_sec,
        limit=body.limit,
    )


@router.post("/region")
def timeline_region(body: RegionBody) -> dict[str, Any]:
    from aive.analysis.frame_metadata import load_frame_index

    frames = load_frame_index(_path(body.path), limit=body.limit)
    return region_summary(frames, body.start_sec, body.end_sec)


@router.post("/frames/full")
def frames_full(body: PathQuery) -> dict[str, Any]:
    return analyze_file(_path(body.path), limit=body.limit)


@router.post("/step-frame")
def step_frame(body: StepFrameBody) -> dict[str, Any]:
    session = sessions.get(body.session_id)
    if not session or session.media_type != "video":
        raise HTTPException(400, "Video session required")
    path = Path(session.source_path or "").expanduser()
    if not path.is_file():
        raise HTTPException(404, "Video file missing on session")

    tl = build_timeline(path, limit=5000)
    frames_raw = tl.get("frames", [])
    if not frames_raw:
        raise HTTPException(400, "No frame index (install ffprobe for I/P/B timeline)")

    from aive.analysis.stream import FrameInfo

    frames = [
        FrameInfo(
            index=f["index"],
            pts=f["pts"],
            dts=None,
            frame_type=f["type"],
            key_frame=f.get("key_frame", False),
            size=f.get("size"),
        )
        for f in frames_raw
    ]

    if body.use_iframe:
        target = nearest_iframe(frames, session.time_sec)
        if not target:
            raise HTTPException(400, "No I-frame found")
        session.frame_index = target.index
        sessions.seek_video(body.session_id, target.pts)
    else:
        current = session.frame_index
        target = frame_at_step(frames, current, body.delta)
        if not target:
            raise HTTPException(400, "Cannot step frame")
        session.frame_index = target.index
        sessions.seek_video(body.session_id, target.pts)

    session = sessions.get(body.session_id)
    return {
        "preview": sessions.frame_to_base64_jpeg(session.frame),
        "frame_index": session.frame_index,
        "time_sec": session.time_sec,
        "filter_chain": [f[0] for f in session.filter_chain],
        "vfr": tl.get("vfr"),
    }


@router.get("/audio/channels")
def audio_channels(path: str) -> dict[str, Any]:
    return probe_multichannel(_path(path))


@router.post("/audio/sync-time")
def audio_sync_time(body: AudioSyncBody) -> dict[str, Any]:
    return audio_time_for_frame(_path(body.path), body.frame_index, body.fps, body.pts_sec)


@router.get("/audio/stream-offset")
def av_offset(path: str) -> dict[str, Any]:
    return stream_sync_offset(_path(path))


@router.post("/video/secondary")
def load_secondary(body: SecondaryVideoBody) -> dict[str, Any]:
    session = sessions.get(body.session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    p = _path(body.path)
    lib = MediaLibrary()
    if lib.classify(p).value != "video":
        raise HTTPException(400, "Not a video file")
    extra = session.metadata.setdefault("additional_videos", [])
    if len(extra) >= lib.max_videos - 1:
        raise HTTPException(400, f"Max {lib.max_videos} videos per examination")
    entry = {"path": str(p), "label": body.label}
    extra.append(entry)
    return {"additional_videos": extra, "count": len(extra)}


@router.get("/video/secondary/{session_id}")
def list_secondary(session_id: str) -> dict[str, Any]:
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"additional_videos": session.metadata.get("additional_videos", [])}
