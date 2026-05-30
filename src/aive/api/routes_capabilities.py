"""Extended forensic capabilities API — hash, seek, audio, annotations, etc."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aive.annotations.store import Annotation, annotation_store
from aive.api.session import sessions
from aive.audio.mux import add_audio_stream, adjust_av_sync, pad_video_to_audio_length
from aive.audio.redaction import adjust_volume, redact_audio_regions
from aive.comparison.session import compare_store
from aive.export.trim import export_frame_list_copy, trim_segment_copy
from aive.forensics.audit import audit_log
from aive.forensics.case import case_store
from aive.forensics.hash_verify import ALGORITHMS, hash_all_algorithms, hash_file, hash_frame, verify_file
from aive.forensics.notes import notes_store
from aive.forensics.secure_copy import secure_copy
from aive.integration.metadata import export_metadata_bundle, ffprobe_full, image_exif
from aive.measurement.tools import Calibration, estimate_speed, measure_distance
from aive.overlays.compose import draw_grid, draw_pip, draw_timestamp
from aive.redaction.privacy import redact_regions
from aive.video.seek import extract_frame_at_index, extract_frame_at_time, extract_iframe_near, get_video_info

router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


def _path(p: str) -> Path:
    path = Path(p).expanduser()
    if not path.exists():
        raise HTTPException(404, f"Not found: {p}")
    return path


class PathBody(BaseModel):
    path: str


class HashVerifyBody(BaseModel):
    path: str
    expected: dict[str, str]


class SecureCopyBody(BaseModel):
    source: str
    destination: str
    report_path: str | None = None


class SeekTimeBody(BaseModel):
    path: str
    time_sec: float


class SeekIndexBody(BaseModel):
    path: str
    frame_index: int


class TrimBody(BaseModel):
    input_path: str
    output_path: str
    start_sec: float
    end_sec: float


class FrameListBody(BaseModel):
    input_path: str
    output_dir: str
    frame_indices: list[int]


class AudioRedactBody(BaseModel):
    input_path: str
    output_path: str
    mute_regions: list[list[float]]


class AudioMuxBody(BaseModel):
    video_path: str
    audio_path: str
    output_path: str


class AudioSyncBody(BaseModel):
    video_path: str
    output_path: str
    audio_delay_ms: float = 0


class NoteBody(BaseModel):
    case_id: str
    author: str
    body: str
    evidence_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class AnnotationBody(BaseModel):
    media_id: str
    type: str
    frame_index: int
    time_sec: float
    points: list[list[float]]
    text: str = ""
    color: list[int] = Field(default_factory=lambda: [0, 255, 255])


class RedactBody(BaseModel):
    session_id: str
    regions: list[dict[str, Any]]


class OverlayBody(BaseModel):
    session_id: str
    timestamp_text: str = ""
    grid: bool = False


class MeasureBody(BaseModel):
    p1: list[float]
    p2: list[float]
    pixels_per_unit: float = 1.0
    unit_name: str = "px"
    delta_time_sec: float | None = None


class CompareCreateBody(BaseModel):
    left_path: str
    right_path: str


class CompareSeekBody(BaseModel):
    session_id: str
    left_time: float | None = None
    right_time: float | None = None


@router.get("/hash/algorithms")
def hash_algorithms() -> dict[str, Any]:
    return {"algorithms": list(ALGORITHMS)}


@router.post("/hash/file")
def hash_file_all(body: PathBody) -> dict[str, Any]:
    p = _path(body.path)
    return {"path": str(p), "hashes": hash_all_algorithms(p)}


@router.post("/hash/verify")
def hash_verify(body: HashVerifyBody) -> dict[str, Any]:
    return verify_file(_path(body.path), body.expected)


@router.get("/hash/frame")
def hash_current_frame(session_id: str, algorithm: str = "sha256") -> dict[str, Any]:
    session = sessions.get(session_id)
    if not session or session.frame is None:
        raise HTTPException(404, "Session not found")
    return {"algorithm": algorithm, "hash": hash_frame(session.frame, algorithm)}


@router.post("/copy/secure")
def copy_secure(body: SecureCopyBody) -> dict[str, Any]:
    src = _path(body.source)
    dst = Path(body.destination).expanduser()
    report = Path(body.report_path).expanduser() if body.report_path else None
    result = secure_copy(src, dst, report)
    case = case_store.active_case()
    audit_log.record(case.case_id, "SECURE_COPY", "examiner", source=str(src), dest=str(dst))
    return result


@router.post("/video/info")
def video_info(body: PathBody) -> dict[str, Any]:
    return get_video_info(_path(body.path))


@router.post("/video/seek/time")
def seek_time(body: SeekTimeBody) -> dict[str, Any]:
    return extract_frame_at_time(_path(body.path), body.time_sec)


@router.post("/video/seek/index")
def seek_index(body: SeekIndexBody) -> dict[str, Any]:
    return extract_frame_at_index(_path(body.path), body.frame_index)


@router.post("/video/seek/iframe")
def seek_iframe(body: SeekTimeBody) -> dict[str, Any]:
    return extract_iframe_near(_path(body.path), body.time_sec)


@router.post("/video/trim")
def trim_video(body: TrimBody) -> dict[str, Any]:
    return trim_segment_copy(_path(body.input_path), Path(body.output_path).expanduser(), body.start_sec, body.end_sec)


@router.post("/video/export-frames")
def export_frames(body: FrameListBody) -> dict[str, Any]:
    return export_frame_list_copy(_path(body.input_path), Path(body.output_dir).expanduser(), body.frame_indices)


@router.post("/audio/redact")
def audio_redact(body: AudioRedactBody) -> dict[str, Any]:
    regions = [(float(a[0]), float(a[1])) for a in body.mute_regions]
    return redact_audio_regions(_path(body.input_path), Path(body.output_path).expanduser(), regions)


@router.post("/audio/mux")
def audio_mux(body: AudioMuxBody) -> dict[str, Any]:
    return add_audio_stream(_path(body.video_path), _path(body.audio_path), Path(body.output_path).expanduser())


@router.post("/audio/sync")
def audio_sync(body: AudioSyncBody) -> dict[str, Any]:
    return adjust_av_sync(_path(body.video_path), Path(body.output_path).expanduser(), body.audio_delay_ms)


class VolumeBody(BaseModel):
    input_path: str
    output_path: str
    volume: float = 1.0


@router.post("/audio/volume")
def audio_volume(body: VolumeBody) -> dict[str, Any]:
    return adjust_volume(_path(body.input_path), Path(body.output_path).expanduser(), body.volume)


@router.post("/audio/pad-video")
def audio_pad(body: AudioMuxBody) -> dict[str, Any]:
    return pad_video_to_audio_length(_path(body.video_path), _path(body.audio_path), Path(body.output_path).expanduser())


@router.get("/notes/{case_id}")
def list_notes(case_id: str) -> dict[str, Any]:
    items = notes_store.list(case_id)
    return {"notes": [n.__dict__ for n in items]}


@router.post("/notes")
def add_note(body: NoteBody) -> dict[str, Any]:
    note = notes_store.add(body.case_id, body.author, body.body, body.evidence_id, body.tags)
    audit_log.record(body.case_id, "NOTE_ADD", body.author)
    return {"note": note.__dict__}


@router.get("/annotations/{media_id}")
def list_annotations(media_id: str) -> dict[str, Any]:
    annotation_store.load()
    return {"annotations": [a.__dict__ for a in annotation_store.list(media_id)]}


@router.post("/annotations")
def add_annotation(body: AnnotationBody) -> dict[str, Any]:
    annotation_store.load()
    ann = Annotation(
        id=str(uuid.uuid4()),
        type=body.type,
        frame_index=body.frame_index,
        time_sec=body.time_sec,
        points=body.points,
        text=body.text,
        color=tuple(body.color[:3]),
    )
    annotation_store.add(body.media_id, ann)
    return {"annotation": ann.__dict__}


@router.post("/examination/redact")
def privacy_redact(body: RedactBody) -> dict[str, Any]:
    session = sessions.get(body.session_id)
    if not session or session.frame is None:
        raise HTTPException(404, "Session not found")
    session.frame = redact_regions(session.frame, body.regions)
    if session.master_frame is not None:
        session.master_frame = redact_regions(session.master_frame, body.regions)
    return {"preview": sessions.frame_to_base64_jpeg(session.frame)}


@router.post("/examination/overlay")
def apply_overlay(body: OverlayBody) -> dict[str, Any]:
    session = sessions.get(body.session_id)
    if not session or session.frame is None:
        raise HTTPException(404, "Session not found")
    frame = session.frame
    if body.timestamp_text:
        frame = draw_timestamp(frame, body.timestamp_text)
    if body.grid:
        frame = draw_grid(frame)
    session.frame = frame
    return {"preview": sessions.frame_to_base64_jpeg(frame)}


@router.post("/measure/distance")
def measure_dist(body: MeasureBody) -> dict[str, Any]:
    cal = Calibration(body.pixels_per_unit, body.unit_name)
    return measure_distance((body.p1[0], body.p1[1]), (body.p2[0], body.p2[1]), cal)


@router.post("/measure/speed")
def measure_spd(body: MeasureBody) -> dict[str, Any]:
    if body.delta_time_sec is None:
        raise HTTPException(400, "delta_time_sec required")
    cal = Calibration(body.pixels_per_unit, body.unit_name)
    return estimate_speed((body.p1[0], body.p1[1]), (body.p2[0], body.p2[1]), body.delta_time_sec, cal)


@router.post("/metadata/export")
def metadata_export(path: str, output_path: str) -> dict[str, Any]:
    return export_metadata_bundle(_path(path), Path(output_path).expanduser())


@router.get("/metadata/ffprobe")
def metadata_ffprobe(path: str) -> dict[str, Any]:
    return ffprobe_full(_path(path))


@router.get("/metadata/exif")
def metadata_exif(path: str) -> dict[str, Any]:
    return image_exif(_path(path))


@router.post("/compare/create")
def compare_create(body: CompareCreateBody) -> dict[str, Any]:
    s = compare_store.create(_path(body.left_path), _path(body.right_path))
    return {"session_id": s.id, "left": s.left_path, "right": s.right_path}


@router.post("/compare/render")
def compare_render(body: CompareSeekBody) -> dict[str, Any]:
    s = compare_store._sessions.get(body.session_id)
    if not s:
        raise HTTPException(404, "Compare session not found")
    if body.left_time is not None:
        s.left_time = body.left_time
    if body.right_time is not None:
        s.right_time = body.right_time
    return compare_store.render(body.session_id)


@router.post("/mpeg/visualize")
def mpeg_visualize(body: SeekTimeBody, mode: str = "macroblock") -> dict[str, Any]:
    from aive.analysis.mpeg_viz import visualize_frame

    return visualize_frame(_path(body.path), body.time_sec, mode)


@router.get("/capture/devices")
def capture_devices() -> dict[str, Any]:
    from aive.capture.devices import list_capture_devices

    return {"devices": list_capture_devices()}


@router.post("/capture/frame")
def capture_frame(device_index: int = 0) -> dict[str, Any]:
    from aive.capture.devices import capture_frame as cap

    return cap(device_index)


class AdvancedVideoBody(BaseModel):
    input_path: str
    output_path: str
    target_fps: float | None = None
    method: str = "fps"
    time_sec: float = 0.0
    duration_sec: float = 3.0
    deinterlace_mode: str = "yadif"
    smoothing: int = 10


@router.post("/advanced/fps-adjust")
def advanced_fps_adjust(body: AdvancedVideoBody) -> dict[str, Any]:
    """R-161 / R-162 — frame dup/removal or manual FPS adjustment."""
    from aive.video.advanced import adjust_frame_rate

    if body.target_fps is None:
        raise HTTPException(400, "target_fps required")
    return adjust_frame_rate(
        _path(body.input_path),
        Path(body.output_path).expanduser(),
        body.target_fps,
        body.method,  # type: ignore[arg-type]
    )


@router.post("/advanced/reverse")
def advanced_reverse(body: AdvancedVideoBody) -> dict[str, Any]:
    """R-165 — reverse video playback."""
    from aive.video.advanced import reverse_video

    return reverse_video(_path(body.input_path), Path(body.output_path).expanduser())


@router.post("/advanced/freeze")
def advanced_freeze(body: AdvancedVideoBody) -> dict[str, Any]:
    """R-164 — freeze frame placeholder clip."""
    from aive.video.advanced import freeze_frame_video

    return freeze_frame_video(
        _path(body.input_path),
        Path(body.output_path).expanduser(),
        body.time_sec,
        body.duration_sec,
    )


@router.post("/advanced/deinterlace")
def advanced_deinterlace(body: AdvancedVideoBody) -> dict[str, Any]:
    """R-150 — full-video deinterlace."""
    from aive.video.advanced import deinterlace_video

    return deinterlace_video(
        _path(body.input_path),
        Path(body.output_path).expanduser(),
        body.deinterlace_mode,  # type: ignore[arg-type]
    )


@router.post("/advanced/stabilize")
def advanced_stabilize(body: AdvancedVideoBody) -> dict[str, Any]:
    """R-160 — video stabilization (vidstab / deshake)."""
    from aive.video.advanced import stabilize_video

    return stabilize_video(
        _path(body.input_path),
        Path(body.output_path).expanduser(),
        body.smoothing,
    )


@router.post("/advanced/perspective-stabilize")
def advanced_perspective_stabilize(body: AdvancedVideoBody) -> dict[str, Any]:
    """R-158 — perspective / rolling-shake correction."""
    from aive.video.advanced import perspective_stabilize_video

    return perspective_stabilize_video(_path(body.input_path), Path(body.output_path).expanduser())

