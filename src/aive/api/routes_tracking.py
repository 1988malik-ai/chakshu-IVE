"""Object tracking and tracking-based video stabilization API."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aive.forensics.audit import audit_log
from aive.forensics.case import case_store

router = APIRouter(prefix="/api/tracking", tags=["tracking"])

_tracker = None


def _tracking_deps():
    from aive.tracking.tracker import HAS_CV2, ObjectTracker, TrackPoint, TrackingMode

    if not HAS_CV2:
        raise HTTPException(
            503,
            "OpenCV not installed. Run: pip install opencv-python-headless",
        )
    global _tracker
    if _tracker is None:
        _tracker = ObjectTracker()
    return ObjectTracker, TrackPoint, TrackingMode, _tracker


def _path(p: str) -> Path:
    path = Path(p).expanduser()
    if not path.exists():
        raise HTTPException(404, f"Not found: {p}")
    return path


def _bbox_tuple(bbox: list[float]) -> tuple[float, float, float, float]:
    if len(bbox) < 4:
        raise HTTPException(400, "bbox must be [x, y, width, height]")
    return float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])


class TrackingSessionBody(BaseModel):
    path: str
    label: str = "target"
    mode: str = "automatic"


class TrackRunBody(BaseModel):
    path: str
    bbox: list[float]
    time_sec: float = 0.0
    end_sec: float | None = None
    tracker_type: str = "KCF"
    label: str = "target"
    tracking_session_id: str | None = None
    max_frames: int = 900
    preview_width: int | None = None
    preview_height: int | None = None


class StabilizeTrackBody(BaseModel):
    input_path: str
    output_path: str
    bbox: list[float] = Field(default_factory=list)
    time_sec: float = 0.0
    end_sec: float | None = None
    tracker_type: str = "KCF"
    smoothing: int = 15
    mode: str = "full"
    crop_padding: float = 0.15
    tracking_session_id: str | None = None
    max_frames: int = 900
    preview_width: int | None = None
    preview_height: int | None = None


@router.post("/session")
def create_tracking_session(body: TrackingSessionBody) -> dict[str, Any]:
    _, _, TrackingMode, tracker = _tracking_deps()
    sid = str(uuid.uuid4())
    mode = TrackingMode(body.mode) if body.mode in {m.value for m in TrackingMode} else TrackingMode.AUTOMATIC
    session = tracker.create_session(sid, str(_path(body.path)), mode, body.label)
    return {"tracking_session_id": session.id, "media_path": session.media_path, "mode": session.mode.value}


@router.get("/session/{tracking_session_id}")
def get_tracking_session(tracking_session_id: str) -> dict[str, Any]:
    _, _, _, tracker = _tracking_deps()
    session = tracker.get_session(tracking_session_id)
    if not session:
        raise HTTPException(404, "Tracking session not found")
    return session.to_dict()


@router.post("/run")
def run_tracking(body: TrackRunBody) -> dict[str, Any]:
    """Track object across video frames from bbox at time_sec."""
    from aive.video.tracking_stabilize import track_video_object

    _, TrackPoint, TrackingMode, tracker = _tracking_deps()
    path = _path(body.path)
    bbox = _bbox_tuple(body.bbox)
    try:
        result = track_video_object(
            path,
            bbox,
            start_sec=body.time_sec,
            end_sec=body.end_sec,
            tracker_type=body.tracker_type,
            max_frames=body.max_frames,
            preview_width=body.preview_width,
            preview_height=body.preview_height,
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e)) from e
    if not result.get("success"):
        raise HTTPException(400, result.get("error", "Tracking failed"))

    sid = body.tracking_session_id or str(uuid.uuid4())
    if not tracker.get_session(sid):
        tracker.create_session(sid, str(path), TrackingMode.AUTOMATIC, body.label)
    session = tracker.get_session(sid)
    if session:
        session.points = [
            TrackPoint(
                p["frame_index"],
                p["x"],
                p["y"],
                p["width"],
                p["height"],
                p.get("confidence", 1.0),
            )
            for p in result["points"]
        ]

    case = case_store.active_case()
    audit_log.record(case.case_id, "OBJECT_TRACK", "examiner", path=str(path), frames=result["frame_count"])
    # Points live in the tracking session — omit from HTTP payload to keep responses fast.
    summary = {k: v for k, v in result.items() if k != "points"}
    return {**summary, "tracking_session_id": sid}


@router.post("/stabilize")
def stabilize_tracking(body: StabilizeTrackBody) -> dict[str, Any]:
    """Export video stabilized to keep tracked object fixed on screen."""
    from aive.video.tracking_stabilize import stabilize_video_object_tracking

    input_path = _path(body.input_path)
    output_path = Path(body.output_path).expanduser()

    points = None
    _, _, _, tracker = _tracking_deps()
    if body.tracking_session_id:
        session = tracker.get_session(body.tracking_session_id)
        if session and session.points:
            points = session.points
    if points is None and not body.bbox:
        raise HTTPException(400, "bbox or tracking_session_id with points required")

    bbox = _bbox_tuple(body.bbox) if body.bbox else (
        points[0].x,
        points[0].y,
        points[0].width,
        points[0].height,
    )
    mode = body.mode if body.mode in ("full", "crop") else "full"
    try:
        result = stabilize_video_object_tracking(
            input_path,
            output_path,
            bbox,
            points=points,
            start_sec=body.time_sec,
            end_sec=body.end_sec,
            tracker_type=body.tracker_type,
            smoothing=body.smoothing,
            mode=mode,  # type: ignore[arg-type]
            crop_padding=body.crop_padding,
            max_frames=body.max_frames,
            preview_width=body.preview_width,
            preview_height=body.preview_height,
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e)) from e
    if not result.get("success"):
        raise HTTPException(400, result.get("error", result.get("stderr", "Stabilization failed")))

    case = case_store.active_case()
    audit_log.record(
        case.case_id,
        "TRACK_STABILIZE",
        "examiner",
        input=str(input_path),
        output=str(output_path),
        mode=mode,
    )
    return result
