"""Extended forensic capabilities API — hash, seek, audio, annotations, etc."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aive.annotations.store import Annotation, annotation_store
from aive.api.examination_payload import examination_preview_fields
from aive.api.session import sessions
from aive.audio.mux import add_audio_stream, adjust_av_sync, pad_video_to_audio_length
from aive.audio.redaction import adjust_volume, redact_audio_regions
from aive.comparison.session import compare_store
from aive.export.trim import export_frame_list_copy, trim_segment_copy
from aive.forensics.audit import audit_log
from aive.forensics.case import case_store
from aive.forensics.hash_verify import ALGORITHMS, hash_all_algorithms, hash_file, hash_frame, verify_file
from aive.project import examination_notes as project_notes
from aive.project.workflow import project_store
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
    mode: str = "mute"


class AudioMuxBody(BaseModel):
    video_path: str
    audio_path: str
    output_path: str
    mode: str = "add"  # add | replace
    audio_codec: str = "aac"
    audio_delay_ms: float = 0
    use_shortest: bool = False
    auto_pad_video: bool = True
    pad_video: bool = False  # legacy alias — forces padding when set
    stream_language: str | None = None
    stream_title: str | None = None


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
    timestamp_position: str = "bottom-right"  # top-left | top-right | bottom-left | bottom-right
    grid: bool = False
    grid_step: int = 50
    grid_style: str = "uniform"  # uniform | thirds | center
    grid_divisions: int | None = None
    pip_path: str | None = None
    pip_time_sec: float = 0.0
    pip_scale: float = 0.28
    pip_position: str = "top-right"


class MeasureBody(BaseModel):
    p1: list[float]
    p2: list[float]
    pixels_per_unit: float = 1.0
    unit_name: str = "px"
    point_uncertainty_px: float = 0.5
    calibration_uncertainty_percent: float = 0.0
    perspective_uncertainty_percent: float = 0.0
    delta_time_sec: float | None = None


class CompareCreateBody(BaseModel):
    left_path: str
    right_path: str


class CompareSeekBody(BaseModel):
    session_id: str
    left_time: float | None = None
    right_time: float | None = None
    mode: str = "side_by_side"
    pip_scale: float = 0.28
    pip_position: str = "top-right"


class CompareExportBody(CompareSeekBody):
    output_path: str


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
    result = redact_audio_regions(
        _path(body.input_path),
        Path(body.output_path).expanduser(),
        regions,
        mode=body.mode,
    )
    if result.get("success"):
        project_store.current.add_step(
            "audio_redact",
            settings={
                "input_path": body.input_path,
                "output_path": body.output_path,
                "mute_regions": body.mute_regions,
                "mode": body.mode,
            },
        )
        case = case_store.active_case()
        audit_log.record(case.case_id, "AUDIO_REDACT", case.examiner or "examiner", body.input_path)
    return result


@router.get("/audio/streams")
def audio_streams(path: str) -> dict[str, Any]:
    """List audio streams on a media file (R-115)."""
    from aive.export.audio import probe_audio_streams

    p = _path(path)
    streams = probe_audio_streams(p)
    return {"path": str(p), "count": len(streams), "streams": streams}


@router.get("/audio/duration-compare")
def audio_duration_compare(video_path: str, audio_path: str) -> dict[str, Any]:
    """Compare video vs audio duration — R-117 auto-padding hint."""
    from aive.audio.duration import compare_av_duration

    return compare_av_duration(_path(video_path), _path(audio_path))


@router.post("/audio/mux")
def audio_mux(body: AudioMuxBody) -> dict[str, Any]:
    """Add or replace audio on video (R-115 / R-117 auto pad)."""
    video = _path(body.video_path)
    audio = _path(body.audio_path)
    out = Path(body.output_path).expanduser()

    result = add_audio_stream(
        video,
        audio,
        out,
        mode=body.mode,
        audio_codec=body.audio_codec,
        audio_delay_ms=body.audio_delay_ms,
        use_shortest=body.use_shortest,
        auto_pad_video=body.auto_pad_video,
        force_pad=body.pad_video,
        stream_language=body.stream_language,
        stream_title=body.stream_title,
    )

    if result.get("success"):
        step_action = "pad_video_to_audio" if result.get("video_padded") else "add_audio_stream"
        project_store.current.add_step(
            step_action,
            settings={**body.model_dump(), "pad_seconds": result.get("pad_seconds", 0)},
            references=[body.audio_path, body.video_path],
        )
        case = case_store.active_case()
        audit_log.record(
            case.case_id,
            "AUDIO_MUX",
            case.examiner or "examiner",
            body.video_path,
            mode=body.mode,
            audio_path=body.audio_path,
            video_padded=result.get("video_padded"),
            pad_seconds=result.get("pad_seconds"),
        )
    return result


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
    """R-117 — pad video to match longer audio."""
    result = pad_video_to_audio_length(
        _path(body.video_path),
        _path(body.audio_path),
        Path(body.output_path).expanduser(),
        keep_original_audio=body.mode != "replace",
        audio_codec=body.audio_codec,
    )
    if result.get("success"):
        project_store.current.add_step(
            "pad_video_to_audio",
            settings=body.model_dump(),
            references=[body.audio_path, body.video_path],
        )
    return result


@router.get("/notes/{case_id}")
def list_notes(case_id: str) -> dict[str, Any]:
    """Legacy case route — returns project notes filtered by case when possible."""
    project_notes.hydrate_from_sidecar()
    items = project_notes.list_notes()
    filtered = [n for n in items if not n.case_id or n.case_id == case_id]
    return {"notes": [n.to_dict() for n in filtered]}


@router.post("/notes")
def add_note(body: NoteBody) -> dict[str, Any]:
    note = project_notes.add_note(
        body.author,
        body.body,
        case_id=body.case_id,
        evidence_id=body.evidence_id,
        tags=body.tags,
    )
    audit_log.record(body.case_id or project_store.current.project_id, "NOTE_ADD", body.author)
    return {"note": note.to_dict()}


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
    return examination_preview_fields(session)


@router.post("/examination/overlay")
def apply_overlay(body: OverlayBody) -> dict[str, Any]:
    import logging

    from aive.comparison.session import _frame_bgr

    log = logging.getLogger("aive.overlay")
    session = sessions.get(body.session_id)
    if not session or session.frame is None:
        raise HTTPException(404, "Session not found")
    try:
        frame = session.frame
        if body.pip_path:
            pip_path = Path(body.pip_path).expanduser()
            if not pip_path.is_file():
                raise HTTPException(400, f"PiP file not found: {body.pip_path}")
            inset = _frame_bgr(pip_path, body.pip_time_sec)
            if inset is None:
                raise HTTPException(400, f"Could not load PiP source: {body.pip_path}")
            frame = draw_pip(
                frame,
                inset,
                scale=body.pip_scale,
                position=body.pip_position,
            )
        if body.timestamp_text:
            frame = draw_timestamp(frame, body.timestamp_text, position=body.timestamp_position)
        if body.grid:
            frame = draw_grid(
                frame,
                step=body.grid_step,
                style=body.grid_style,
                divisions=body.grid_divisions,
            )
        session.frame = frame
        return examination_preview_fields(session)
    except HTTPException:
        raise
    except Exception as e:
        log.exception("overlay failed session=%s pip=%s", body.session_id, body.pip_path)
        raise HTTPException(500, f"Overlay failed: {e}") from e


@router.post("/measure/distance")
def measure_dist(body: MeasureBody) -> dict[str, Any]:
    cal = Calibration(
        body.pixels_per_unit,
        body.unit_name,
        body.point_uncertainty_px,
        body.calibration_uncertainty_percent,
        body.perspective_uncertainty_percent,
    )
    return measure_distance((body.p1[0], body.p1[1]), (body.p2[0], body.p2[1]), cal)


@router.post("/measure/speed")
def measure_spd(body: MeasureBody) -> dict[str, Any]:
    if body.delta_time_sec is None:
        raise HTTPException(400, "delta_time_sec required")
    cal = Calibration(
        body.pixels_per_unit,
        body.unit_name,
        body.point_uncertainty_px,
        body.calibration_uncertainty_percent,
        body.perspective_uncertainty_percent,
    )
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


@router.get("/compare/{session_id}")
def compare_get(session_id: str) -> dict[str, Any]:
    s = compare_store.get(session_id)
    if not s:
        raise HTTPException(404, "Compare session not found")
    return {
        "session_id": s.id,
        "left_path": s.left_path,
        "right_path": s.right_path,
        "left_time": s.left_time,
        "right_time": s.right_time,
    }


@router.post("/compare/render")
def compare_render(body: CompareSeekBody) -> dict[str, Any]:
    import logging

    log = logging.getLogger("aive.compare")
    s = compare_store.get(body.session_id)
    if not s:
        raise HTTPException(404, "Compare session not found")
    try:
        if body.left_time is not None:
            s.left_time = body.left_time
        if body.right_time is not None:
            s.right_time = body.right_time
        mode = body.mode if body.mode in ("side_by_side", "pip") else "side_by_side"
        result = compare_store.render(
            body.session_id,
            mode=mode,
            pip_scale=body.pip_scale,
            pip_position=body.pip_position,
        )
        if not result.get("success"):
            log.warning(
                "compare/render failed session=%s left=%s right=%s err=%s",
                body.session_id,
                s.left_path,
                s.right_path,
                result.get("error"),
            )
            raise HTTPException(400, result.get("error", "Compare render failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.exception(
            "compare/render error session=%s left=%s right=%s",
            body.session_id,
            s.left_path,
            s.right_path,
        )
        raise HTTPException(500, f"Compare render failed: {e}") from e


@router.post("/compare/export-image")
def compare_export_image(body: CompareExportBody) -> dict[str, Any]:
    import logging

    log = logging.getLogger("aive.compare")
    s = compare_store.get(body.session_id)
    if not s:
        raise HTTPException(404, "Compare session not found")
    try:
        if body.left_time is not None:
            s.left_time = body.left_time
        if body.right_time is not None:
            s.right_time = body.right_time
        mode = body.mode if body.mode in ("side_by_side", "pip") else "side_by_side"
        output_path = Path(body.output_path).expanduser()
        if output_path.suffix.lower() not in {".jpg", ".jpeg"}:
            output_path = output_path.with_suffix(".jpg")
        result = compare_store.export_image(
            body.session_id,
            output_path,
            mode=mode,
            pip_scale=body.pip_scale,
            pip_position=body.pip_position,
        )
        if not result.get("success"):
            raise HTTPException(400, result.get("error", "Compare export failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.exception(
            "compare/export-image error session=%s left=%s right=%s output=%s",
            body.session_id,
            s.left_path,
            s.right_path,
            body.output_path,
        )
        raise HTTPException(500, f"Compare export failed: {e}") from e


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


class TrackingStabilizeBody(BaseModel):
    input_path: str
    output_path: str
    bbox: list[float]
    time_sec: float = 0.0
    end_sec: float | None = None
    tracker_type: str = "CSRT"
    smoothing: int = 15
    mode: str = "full"
    crop_padding: float = 0.15
    max_frames: int = 5000


@router.post("/advanced/tracking-stabilize")
def advanced_tracking_stabilize(body: TrackingStabilizeBody) -> dict[str, Any]:
    """R-160 — object-tracking-based video stabilization."""
    from aive.video.tracking_stabilize import stabilize_video_object_tracking

    if len(body.bbox) < 4:
        raise HTTPException(400, "bbox must be [x, y, width, height]")
    bbox = (float(body.bbox[0]), float(body.bbox[1]), float(body.bbox[2]), float(body.bbox[3]))
    mode = body.mode if body.mode in ("full", "crop") else "full"
    result = stabilize_video_object_tracking(
        _path(body.input_path),
        Path(body.output_path).expanduser(),
        bbox,
        start_sec=body.time_sec,
        end_sec=body.end_sec,
        tracker_type=body.tracker_type,
        smoothing=body.smoothing,
        mode=mode,  # type: ignore[arg-type]
        crop_padding=body.crop_padding,
        max_frames=body.max_frames,
    )
    if not result.get("success"):
        raise HTTPException(400, result.get("error", result.get("stderr", "Failed")))
    case = case_store.active_case()
    audit_log.record(case.case_id, "TRACK_STABILIZE", "examiner", output=body.output_path)
    return result


class PanoramaConvertBody(BaseModel):
    input_path: str
    output_path: str
    source_type: str = "fisheye"
    output_type: str = "equirectangular"
    fov_deg: float = 180.0
    fisheye_model: str = "equidistant"
    yaw_deg: float = 0.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    fov_h_deg: float = 90.0
    fov_v_deg: float = 60.0
    out_width: int | None = None
    out_height: int | None = None


@router.post("/advanced/panorama-convert")
def advanced_panorama_convert(body: PanoramaConvertBody) -> dict[str, Any]:
    """R-152 — convert omnidirectional / 360° image to panoramic output."""
    from aive.panorama import convert_omnidirectional_file

    result = convert_omnidirectional_file(
        _path(body.input_path),
        Path(body.output_path).expanduser(),
        source_type=body.source_type,
        output_type=body.output_type,
        fov_deg=body.fov_deg,
        fisheye_model=body.fisheye_model,  # type: ignore[arg-type]
        yaw_deg=body.yaw_deg,
        pitch_deg=body.pitch_deg,
        roll_deg=body.roll_deg,
        fov_h_deg=body.fov_h_deg,
        fov_v_deg=body.fov_v_deg,
        out_width=body.out_width,
        out_height=body.out_height,
    )
    if not result.get("success"):
        raise HTTPException(400, result.get("error", "Panorama conversion failed"))
    case = case_store.active_case()
    audit_log.record(
        case.case_id,
        "PANORAMA_CONVERT",
        "examiner",
        input=body.input_path,
        output=body.output_path,
        source_type=body.source_type,
        output_type=body.output_type,
    )
    return result


class PanoramaSessionBody(BaseModel):
    session_id: str
    output_path: str
    source_type: str = "fisheye"
    output_type: str = "equirectangular"
    fov_deg: float = 180.0
    fisheye_model: str = "equidistant"
    yaw_deg: float = 0.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    fov_h_deg: float = 90.0
    fov_v_deg: float = 60.0
    out_width: int | None = None
    out_height: int | None = None


@router.post("/advanced/panorama-session")
def advanced_panorama_session(body: PanoramaSessionBody) -> dict[str, Any]:
    """Convert current examination frame (image or video still) to panoramic JPEG."""
    from aive.imaging import save_bgr_jpeg
    from aive.panorama import convert_omnidirectional

    session = sessions.get(body.session_id)
    if not session or session.master_frame is None:
        raise HTTPException(400, "No frame loaded in session")
    out = Path(body.output_path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = convert_omnidirectional(
            session.master_frame,
            source_type=body.source_type,
            output_type=body.output_type,
            fov_deg=body.fov_deg,
            fisheye_model=body.fisheye_model,  # type: ignore[arg-type]
            yaw_deg=body.yaw_deg,
            pitch_deg=body.pitch_deg,
            roll_deg=body.roll_deg,
            fov_h_deg=body.fov_h_deg,
            fov_v_deg=body.fov_v_deg,
            out_width=body.out_width,
            out_height=body.out_height,
        )
    except Exception as e:
        raise HTTPException(400, str(e)) from e
    save_bgr_jpeg(out, result)
    case = case_store.active_case()
    audit_log.record(
        case.case_id,
        "PANORAMA_CONVERT",
        "examiner",
        session_id=body.session_id,
        output=str(out),
        source_type=body.source_type,
        output_type=body.output_type,
    )
    return {
        "success": True,
        "output_path": str(out),
        "width": int(result.shape[1]),
        "height": int(result.shape[0]),
        "source_type": body.source_type,
        "output_type": body.output_type,
    }


@router.post("/advanced/perspective-stabilize")
def advanced_perspective_stabilize(body: AdvancedVideoBody) -> dict[str, Any]:
    """R-158 — perspective / rolling-shake correction."""
    from aive.video.advanced import perspective_stabilize_video

    return perspective_stabilize_video(_path(body.input_path), Path(body.output_path).expanduser())


class ClipboardTextBody(BaseModel):
    text: str


class SubtitleBurnBody(BaseModel):
    video_path: str
    subtitle_path: str
    output_path: str
    font_size: int = 22
    font_name: str = "Arial"
    margin_v: int = 28
    outline: int = 2
    alignment: int = 2


class MergeAvBody(BaseModel):
    video_path: str
    audio_path: str
    output_path: str
    audio_delay_ms: float = 0.0


class MergeVideosBody(BaseModel):
    paths: list[str]
    output_path: str
    reencode: bool = True


class StreamSyncBody(BaseModel):
    path_a: str
    path_b: str
    time_a: float = 0.0
    time_b: float = 0.0
    search_sec: float = 2.0


@router.get("/clipboard/frame")
def clipboard_frame(session_id: str, include_hash: bool = True) -> dict[str, Any]:
    """R-134 — frame payload for clipboard / office paste."""
    from aive.export.clipboard import frame_clipboard_payload

    session = sessions.get(session_id)
    if not session or session.frame is None:
        raise HTTPException(404, "No frame in session")
    return frame_clipboard_payload(session.frame, include_hash)


@router.post("/clipboard/text")
def clipboard_text(body: ClipboardTextBody) -> dict[str, Any]:
    from aive.export.clipboard import text_clipboard_payload

    return text_clipboard_payload(body.text)


class SubtitlePathBody(BaseModel):
    path: str
    limit: int = 2000


class SubtitleOverlaySessionBody(BaseModel):
    session_id: str
    subtitle_path: str
    time_sec: float | None = None
    font_size: int = 22
    margin_v: int = 28
    apply_to_enhanced: bool = True


@router.post("/subtitles/parse")
def subtitles_parse(body: SubtitlePathBody) -> dict[str, Any]:
    """R-120 — parse SRT or SMI subtitle file."""
    from aive.subtitles.renderer import SubtitleParser, cues_to_dicts

    path = _path(body.path)
    cues = SubtitleParser.load(path)
    return {
        "path": str(path),
        "format": SubtitleParser.detect_format(path),
        "count": len(cues),
        "cues": cues_to_dicts(cues, body.limit),
    }


@router.get("/subtitles/cue-at-time")
def subtitles_cue_at_time(path: str, time_sec: float) -> dict[str, Any]:
    from aive.subtitles.renderer import SubtitleParser, cue_at_time

    p = _path(path)
    cues = SubtitleParser.load(p)
    cue = cue_at_time(cues, time_sec)
    if not cue:
        return {"active": False, "time_sec": time_sec}
    return {
        "active": True,
        "time_sec": time_sec,
        "cue": {"start": cue.start_sec, "end": cue.end_sec, "text": cue.text},
    }


@router.post("/subtitles/overlay-session")
def subtitles_overlay_session(body: SubtitleOverlaySessionBody) -> dict[str, Any]:
    """R-120 — render active subtitle cue onto the current examination frame."""
    from aive.overlays.compose import draw_subtitle_cue
    from aive.subtitles.renderer import SubtitleParser, cue_at_time

    session = sessions.get(body.session_id)
    if not session or session.frame is None:
        raise HTTPException(404, "No frame in session")
    cues = SubtitleParser.load(_path(body.subtitle_path))
    t = body.time_sec if body.time_sec is not None else session.time_sec
    cue = cue_at_time(cues, t)
    if not cue:
        return {
            **examination_preview_fields(session),
            "subtitle_active": False,
            "subtitle_time_sec": t,
        }
    h, w = session.frame.shape[:2]
    scale = max(0.45, w / 1600) * (body.font_size / 22.0)
    frame = draw_subtitle_cue(
        session.frame,
        cue.text,
        font_scale=scale,
        margin_v=body.margin_v,
    )
    if body.apply_to_enhanced:
        session.frame = frame
    else:
        session.master_frame = frame
    project_store.current.add_step(
        "subtitle_overlay",
        settings={"subtitle_path": body.subtitle_path, "time_sec": t, "text": cue.text[:120]},
    )
    return {
        **examination_preview_fields(session),
        "subtitle_active": True,
        "subtitle_time_sec": t,
        "subtitle_text": cue.text,
        "subtitle_start": cue.start_sec,
        "subtitle_end": cue.end_sec,
    }


@router.post("/subtitles/burn")
def subtitles_burn(body: SubtitleBurnBody) -> dict[str, Any]:
    """R-121 — styled subtitle burn-in (SRT / SMI)."""
    from aive.subtitles.renderer import SubtitleParser, burn_subtitles

    style = {
        "font_size": body.font_size,
        "font_name": body.font_name,
        "margin_v": body.margin_v,
        "outline": body.outline,
        "alignment": body.alignment,
    }
    sub_path = _path(body.subtitle_path)
    result = burn_subtitles(
        _path(body.video_path),
        sub_path,
        Path(body.output_path).expanduser(),
        style,
    )
    if result.get("success"):
        project_store.current.add_step(
            "subtitle_burn",
            settings={
                "video_path": body.video_path,
                "subtitle_path": body.subtitle_path,
                "format": SubtitleParser.detect_format(sub_path),
                "output_path": body.output_path,
            },
        )
    return result


@router.post("/merge/av")
def merge_av(body: MergeAvBody) -> dict[str, Any]:
    """R-173 — merge video + audio streams."""
    from aive.video.merge import merge_av_streams

    return merge_av_streams(
        _path(body.video_path),
        _path(body.audio_path),
        Path(body.output_path).expanduser(),
        body.audio_delay_ms,
    )


@router.post("/merge/videos")
def merge_videos(body: MergeVideosBody) -> dict[str, Any]:
    """R-173 — concatenate multiple videos."""
    from aive.video.merge import concat_videos

    if len(body.paths) < 2:
        raise HTTPException(400, "At least two video paths required")
    paths = [_path(p) for p in body.paths]
    return concat_videos(paths, Path(body.output_path).expanduser(), body.reencode)


@router.post("/sync/similarity")
def sync_similarity(body: StreamSyncBody) -> dict[str, Any]:
    """R-172 — frame similarity and offset search."""
    from aive.analysis.sync import compare_streams_at_time, find_best_offset

    pa, pb = _path(body.path_a), _path(body.path_b)
    if body.search_sec > 0 and body.time_a == body.time_b:
        return find_best_offset(pa, pb, body.time_a, body.search_sec)
    return compare_streams_at_time(pa, pb, body.time_a, body.time_b)
