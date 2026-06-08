"""Phase 3 — interactive markup, redaction, measurement."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from aive.annotations.store import Annotation, annotation_store, snap_points
from aive.annotations.media_id import canonical_media_id
from aive.api.session import sessions
from aive.forensics.audit import audit_log
from aive.forensics.case import case_store
from aive.measurement.store import measurement_store
from aive.measurement.tools import Calibration, estimate_speed, measure_distance
from aive.redaction.privacy import redact_regions

router = APIRouter(prefix="/api/markup", tags=["markup"])


class AnnotationBody(BaseModel):
    media_id: str
    type: str
    frame_index: int
    time_sec: float = 0.0
    points: list[list[float]]
    text: str = ""
    color: list[int] = Field(default_factory=lambda: [0, 255, 255])
    group_id: str | None = None
    snap_grid: int = 0
    image_width: int | None = None
    image_height: int | None = None


class RenderBody(BaseModel):
    session_id: str
    media_id: str
    frame_index: int = 0
    include_annotations: bool = True
    persist: bool = False


class RedactBody(BaseModel):
    session_id: str
    regions: list[dict[str, Any]]
    mode: str = "pixelate"


class MeasureDrawBody(BaseModel):
    session_id: str
    media_id: str
    frame_index: int
    time_sec: float = 0.0
    p1: list[float]
    p2: list[float]
    pixels_per_unit: float = 1.0
    unit_name: str = "px"
    delta_time_sec: float | None = None
    group_id: str | None = None
    snap_grid: int = 0
    image_width: int | None = None
    image_height: int | None = None


@router.get("/annotations")
def list_annotations(
    media_id: str = Query(..., description="Evidence key or storage path"),
    frame_index: int | None = Query(None),
) -> dict[str, Any]:
    annotation_store.load()
    items = annotation_store.list(media_id)
    if frame_index is not None:
        items = [a for a in items if a.frame_index == frame_index]
    return {
        "annotations": [a.__dict__ for a in items],
        "groups": annotation_store.list_groups(media_id),
    }


@router.get("/annotations/{media_id}")
def list_annotations_legacy(media_id: str, frame_index: int | None = None) -> dict[str, Any]:
    """Legacy path route — prefer GET /annotations?media_id=… for paths with slashes."""
    return list_annotations(media_id=media_id, frame_index=frame_index)


@router.post("/annotations")
def add_annotation(body: AnnotationBody) -> dict[str, Any]:
    annotation_store.load()
    points = body.points
    if body.snap_grid and body.image_width and body.image_height:
        points = snap_points(points, body.image_width, body.image_height, body.snap_grid)
    ann = Annotation(
        id=str(uuid.uuid4()),
        type=body.type,
        frame_index=body.frame_index,
        time_sec=body.time_sec,
        points=points,
        text=body.text,
        color=tuple(body.color[:3]),
        group_id=body.group_id,
        metadata={
            "image_width": body.image_width,
            "image_height": body.image_height,
        },
    )
    media_key = canonical_media_id(body.media_id)
    annotation_store.add(media_key, ann)
    case = case_store.active_case()
    audit_log.record(case.case_id, "ANNOTATION_ADD", "examiner", type=body.type, media_id=body.media_id)
    return {"annotation": ann.__dict__}


@router.delete("/annotations/{annotation_id}")
def delete_annotation(
    annotation_id: str,
    media_id: str = Query(..., description="Evidence key or storage path"),
) -> dict[str, Any]:
    annotation_store.load()
    ok = annotation_store.delete(media_id, annotation_id)
    if not ok:
        raise HTTPException(404, "Annotation not found")
    return {"deleted": True}


@router.post("/render")
def render_markup(body: RenderBody) -> dict[str, Any]:
    session = sessions.get(body.session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if session.frame is None and session.master_frame is not None:
        session.frame = session.master_frame.copy()
    if session.frame is None:
        raise HTTPException(404, "No frame loaded — ingest evidence first")
    frame = session.frame.copy()
    if body.include_annotations:
        annotation_store.load()
        media_key = canonical_media_id(body.media_id)
        frame = annotation_store.render_on_frame(frame, media_key, body.frame_index)
    session.frame = frame
    if body.persist and session.master_frame is not None:
        session.master_frame = frame.copy()
    return {"preview": sessions.frame_to_base64_jpeg(frame), "persisted": body.persist}


@router.post("/redact")
def apply_redact(body: RedactBody) -> dict[str, Any]:
    session = sessions.get(body.session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if session.frame is None and session.master_frame is not None:
        session.frame = session.master_frame.copy()
    if session.frame is None:
        raise HTTPException(404, "No frame loaded — ingest evidence first")
    regions = [{**r, "mode": body.mode} for r in body.regions]
    session.frame = redact_regions(session.frame, regions)
    session.master_frame = redact_regions(session.master_frame, regions) if session.master_frame is not None else session.frame
    case = case_store.active_case()
    audit_log.record(case.case_id, "REDACT_APPLY", "examiner", regions=len(regions))
    return {"preview": sessions.frame_to_base64_jpeg(session.frame)}


@router.post("/measure")
def measure_and_save(body: MeasureDrawBody) -> dict[str, Any]:
    session = sessions.get(body.session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if session.frame is None and session.master_frame is not None:
        session.frame = session.master_frame.copy()
    if session.frame is None:
        raise HTTPException(404, "No frame loaded — ingest evidence first")

    p1, p2 = body.p1, body.p2
    if body.snap_grid and body.image_width and body.image_height:
        p1, p2 = snap_points([p1, p2], body.image_width, body.image_height, body.snap_grid)

    cal = Calibration(body.pixels_per_unit, body.unit_name)
    result = measure_distance((p1[0], p1[1]), (p2[0], p2[1]), cal)
    if body.delta_time_sec:
        result["speed"] = estimate_speed((p1[0], p1[1]), (p2[0], p2[1]), body.delta_time_sec, cal)

    label = f"{result['distance']:.2f} {result['unit']}"
    ann = Annotation(
        id=str(uuid.uuid4()),
        type="measure",
        frame_index=body.frame_index,
        time_sec=body.time_sec,
        points=[p1, p2],
        text=label,
        group_id=body.group_id,
        metadata={
            "distance_label": label,
            "image_width": body.image_width,
            "image_height": body.image_height,
            **result,
        },
    )
    annotation_store.load()
    media_key = canonical_media_id(body.media_id)
    annotation_store.add(media_key, ann)
    measurement_store.add(media_key, body.frame_index, p1, p2, result, label=label)

    frame = annotation_store.render_on_frame(session.frame, media_key, body.frame_index)
    session.frame = frame
    return {"preview": sessions.frame_to_base64_jpeg(frame), "measurement": result, "annotation": ann.__dict__}


@router.get("/measurements")
def list_measurements(media_id: str = Query(..., description="Evidence key or storage path")) -> dict[str, Any]:
    return {"measurements": [m.__dict__ for m in measurement_store.list(media_id)]}


@router.get("/measurements/{media_id}")
def list_measurements_legacy(media_id: str) -> dict[str, Any]:
    return list_measurements(media_id=media_id)
