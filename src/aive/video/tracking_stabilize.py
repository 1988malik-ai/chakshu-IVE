"""
Object-tracking-based video stabilization.

Tracks a user-selected region across frames, smooths motion, and warps video
so the tracked object stays fixed on screen (full-frame or cropped export).

Author: Mohit M
"""

from __future__ import annotations

import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any, Iterator, Literal

import numpy as np

from aive.codecs.ffmpeg_bin import require_ffmpeg
from aive.imaging import HAS_CV2
from aive.tracking.tracker import TrackPoint

if HAS_CV2:
    import cv2

DEFAULT_TRACK_SEC = 30.0
DEFAULT_MAX_FRAMES = 900


def _require_cv2() -> None:
    if not HAS_CV2:
        raise RuntimeError("OpenCV required for object-tracking stabilization (pip install opencv-python)")


def _create_tracker(tracker_type: str = "KCF") -> tuple[Any, str]:
    _require_cv2()
    tried: list[str] = []
    for name in (tracker_type, "KCF", "MOSSE", "CSRT", "MIL"):
        if name in tried:
            continue
        tried.append(name)
        for mod in (cv2, getattr(cv2, "legacy", None)):
            if mod is None:
                continue
            ctor = getattr(mod, f"Tracker{name}_create", None)
            if callable(ctor):
                return ctor(), name
    raise RuntimeError(
        "No OpenCV tracker available. Install: pip install opencv-contrib-python-headless"
    )


def _scale_bbox(
    bbox: tuple[float, float, float, float],
    preview_w: int | None,
    preview_h: int | None,
    video_w: int,
    video_h: int,
) -> tuple[float, float, float, float]:
    x, y, w, h = bbox
    if not preview_w or not preview_h or preview_w <= 0 or preview_h <= 0:
        return bbox
    if preview_w == video_w and preview_h == video_h:
        return bbox
    sx = video_w / preview_w
    sy = video_h / preview_h
    return (x * sx, y * sy, w * sx, h * sy)


def _video_span(path: Path, cap: "cv2.VideoCapture") -> tuple[float, int, int]:
    """Return (fps, total_frames, duration_sec) with ffprobe fallbacks."""
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = total / fps if total > 0 and fps > 0 else 0.0
    if total <= 0 or duration <= 0:
        try:
            from aive.video.seek import get_video_info

            info = get_video_info(path)
            if info.get("fps"):
                fps = float(info["fps"])
            if info.get("duration"):
                duration = float(info["duration"])
                if total <= 0 and fps > 0:
                    total = int(round(duration * fps))
            if info.get("frame_count") and int(info["frame_count"]) > 0:
                total = int(info["frame_count"])
        except Exception:
            pass
    if duration <= 0 and total > 0 and fps > 0:
        duration = total / fps
    return fps, total, duration


def _resolve_end_frame(
    *,
    start_frame: int,
    start_sec: float,
    end_sec: float | None,
    fps: float,
    total: int,
    duration: float,
    max_frames: int,
) -> int:
    if end_sec is not None and end_sec > start_sec:
        end_frame = int(round(end_sec * fps))
    else:
        end_frame = int(round((start_sec + DEFAULT_TRACK_SEC) * fps))
    if duration > 0:
        end_frame = min(end_frame, int(round(duration * fps)) - 1)
    if total > 0:
        end_frame = min(end_frame, total - 1)
    end_frame = min(end_frame, start_frame + max(1, max_frames) - 1)
    return max(start_frame, end_frame)


def _seek_capture(cap: "cv2.VideoCapture", start_sec: float, start_frame: int) -> None:
    cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, start_sec) * 1000)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)


def _fill_track_gaps(points: list[TrackPoint], start_frame: int, end_frame: int) -> list[TrackPoint]:
    if not points:
        return []
    by_frame = {p.frame_index: p for p in points}
    filled: list[TrackPoint] = []
    last = points[0]
    for fi in range(start_frame, end_frame + 1):
        if fi in by_frame:
            last = by_frame[fi]
        filled.append(
            TrackPoint(fi, last.x, last.y, last.width, last.height, last.confidence)
        )
    return filled


def _encode_with_ffmpeg(
    ffmpeg: str,
    frames: Iterator[np.ndarray],
    width: int,
    height: int,
    fps: float,
    output_path: Path,
) -> tuple[bool, str]:
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-s",
        f"{width}x{height}",
        "-pix_fmt",
        "bgr24",
        "-r",
        str(max(fps, 1.0)),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
    )
    assert proc.stdin is not None
    stderr_chunks: list[bytes] = []

    def _drain_stderr() -> None:
        if proc.stderr:
            stderr_chunks.append(proc.stderr.read())

    reader = threading.Thread(target=_drain_stderr, daemon=True)
    reader.start()
    try:
        for frame in frames:
            if frame.shape[0] != height or frame.shape[1] != width:
                frame = cv2.resize(frame, (width, height))
            proc.stdin.write(frame.astype(np.uint8).tobytes())
    finally:
        proc.stdin.close()
    code = proc.wait()
    reader.join(timeout=5)
    err = b"".join(stderr_chunks).decode("utf-8", errors="replace")
    return code == 0 and output_path.is_file() and output_path.stat().st_size > 0, err


def _mux_audio(
    ffmpeg: str,
    video_path: Path,
    audio_src: Path,
    output_path: Path,
    start_sec: float,
) -> tuple[bool, str]:
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video_path),
        "-ss",
        str(max(0.0, start_sec)),
        "-i",
        str(audio_src),
        "-map",
        "0:v:0",
        "-map",
        "1:a?",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-shortest",
        str(output_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0, (r.stderr or "")[-800:]


def _smooth(values: list[float], window: int) -> list[float]:
    if window <= 1 or len(values) < 2:
        return values
    w = max(1, min(window, len(values)))
    kernel = np.ones(w, dtype=np.float64) / w
    padded = np.pad(values, (w // 2, w - 1 - w // 2), mode="edge")
    return [float(v) for v in np.convolve(padded, kernel, mode="valid")]


def track_video_object(
    input_path: Path,
    bbox: tuple[float, float, float, float],
    *,
    start_sec: float = 0.0,
    end_sec: float | None = None,
    tracker_type: str = "KCF",
    max_frames: int = DEFAULT_MAX_FRAMES,
    preview_width: int | None = None,
    preview_height: int | None = None,
) -> dict[str, Any]:
    """Run OpenCV tracker from start_sec through end_sec (or clip end)."""
    _require_cv2()
    path = input_path.expanduser().resolve()
    if not path.is_file():
        return {"success": False, "error": f"Not found: {path}"}

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"success": False, "error": "Could not open video"}

    fps, total, duration = _video_span(path, cap)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

    start_frame = max(0, int(round(start_sec * fps)))
    end_frame = _resolve_end_frame(
        start_frame=start_frame,
        start_sec=start_sec,
        end_sec=end_sec,
        fps=fps,
        total=total,
        duration=duration,
        max_frames=max_frames,
    )

    bbox = _scale_bbox(bbox, preview_width, preview_height, width, height)
    _seek_capture(cap, start_sec, start_frame)
    ok, frame = cap.read()
    if not ok or frame is None:
        cap.release()
        return {"success": False, "error": "Could not read start frame — try Load Frame at Time first"}

    x, y, w, h = bbox
    init_bbox = (
        int(round(max(0, x))),
        int(round(max(0, y))),
        int(max(4, round(min(w, width - x)))),
        int(max(4, round(min(h, height - y)))),
    )
    tracker, used_tracker = _create_tracker(tracker_type)
    try:
        tracker.init(frame, init_bbox)
    except Exception as e:
        cap.release()
        return {"success": False, "error": f"Tracker init failed: {e}"}

    points: list[TrackPoint] = [
        TrackPoint(start_frame, float(init_bbox[0]), float(init_bbox[1]), float(init_bbox[2]), float(init_bbox[3]))
    ]
    last_box = init_bbox
    frame_idx = start_frame + 1

    while frame_idx <= end_frame:
        ok, frame = cap.read()
        if not ok or frame is None:
            break
        success, box = tracker.update(frame)
        if success:
            bx, by, bw, bh = box
            last_box = (int(bx), int(by), int(bw), int(bh))
            points.append(TrackPoint(frame_idx, float(bx), float(by), float(bw), float(bh)))
        else:
            bx, by, bw, bh = last_box
            points.append(TrackPoint(frame_idx, float(bx), float(by), float(bw), float(bh)))
        frame_idx += 1

    cap.release()
    end_frame = points[-1].frame_index if points else start_frame
    points = _fill_track_gaps(points, start_frame, end_frame)
    track_span_sec = round((end_frame - start_frame) / fps, 2) if fps else 0
    return {
        "success": True,
        "fps": fps,
        "width": width,
        "height": height,
        "start_frame": start_frame,
        "end_frame": end_frame,
        "frame_count": len(points),
        "track_span_sec": track_span_sec,
        "tracker_type": used_tracker,
        "points": [
            {
                "frame_index": p.frame_index,
                "time_sec": round(p.frame_index / fps, 4) if fps else 0,
                "x": p.x,
                "y": p.y,
                "width": p.width,
                "height": p.height,
                "confidence": p.confidence,
            }
            for p in points
        ],
    }


def _offsets_from_points(
    points: list[TrackPoint],
    width: int,
    height: int,
    *,
    smoothing: int = 15,
    anchor: Literal["first", "center"] = "first",
) -> tuple[list[float], list[float], float, float]:
    if not points:
        return [], [], width / 2, height / 2
    centers = [(p.x + p.width / 2, p.y + p.height / 2) for p in points]
    if anchor == "center":
        ref_x = width / 2
        ref_y = height / 2
    else:
        ref_x, ref_y = centers[0]
    raw_dx = [ref_x - cx for cx, _ in centers]
    raw_dy = [ref_y - cy for _, cy in centers]
    return _smooth(raw_dx, smoothing), _smooth(raw_dy, smoothing), ref_x, ref_y


def stabilize_video_object_tracking(
    input_path: Path,
    output_path: Path,
    bbox: tuple[float, float, float, float],
    *,
    points: list[TrackPoint] | None = None,
    start_sec: float = 0.0,
    end_sec: float | None = None,
    tracker_type: str = "KCF",
    smoothing: int = 15,
    mode: Literal["full", "crop"] = "full",
    crop_padding: float = 0.15,
    max_frames: int = DEFAULT_MAX_FRAMES,
    preview_width: int | None = None,
    preview_height: int | None = None,
) -> dict[str, Any]:
    """Track (or reuse points), warp frames, encode stabilized clip with audio."""
    _require_cv2()
    path = input_path.expanduser().resolve()
    out = output_path.expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)

    if points is None:
        track_result = track_video_object(
            path,
            bbox,
            start_sec=start_sec,
            end_sec=end_sec,
            tracker_type=tracker_type,
            max_frames=max_frames,
            preview_width=preview_width,
            preview_height=preview_height,
        )
        if not track_result.get("success"):
            return track_result
        points = [
            TrackPoint(p["frame_index"], p["x"], p["y"], p["width"], p["height"], p.get("confidence", 1.0))
            for p in track_result["points"]
        ]
        fps = track_result["fps"]
        width = track_result["width"]
        height = track_result["height"]
        start_frame = track_result["start_frame"]
        end_frame = track_result["end_frame"]
    else:
        cap = cv2.VideoCapture(str(path))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        cap.release()
        start_frame = points[0].frame_index
        end_frame = points[-1].frame_index
        start_sec = start_frame / fps if fps else start_sec

    points = _fill_track_gaps(points, start_frame, end_frame)
    if len(points) < 2:
        return {"success": False, "error": "Need at least 2 frames — use a longer clip or adjust the box"}

    dx_list, dy_list, _, _ = _offsets_from_points(points, width, height, smoothing=smoothing)

    crop_w = crop_h = None
    if mode == "crop":
        max_w = max(p.width for p in points)
        max_h = max(p.height for p in points)
        pad = 1.0 + max(0.0, crop_padding)
        crop_w = int(min(width, max(64, max_w * pad)))
        crop_h = int(min(height, max(64, max_h * pad)))

    out_w, out_h = (crop_w, crop_h) if mode == "crop" and crop_w and crop_h else (width, height)

    cap = cv2.VideoCapture(str(path))
    _seek_capture(cap, start_sec, start_frame)

    def frame_generator() -> Iterator[np.ndarray]:
        for pi, pt in enumerate(points):
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            dx = dx_list[pi]
            dy = dy_list[pi]
            m = np.float32([[1, 0, dx], [0, 1, dy]])
            warped = cv2.warpAffine(
                frame,
                m,
                (width, height),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REPLICATE,
            )
            if mode == "crop" and crop_w and crop_h:
                cx = pt.x + pt.width / 2 + dx
                cy = pt.y + pt.height / 2 + dy
                x0 = int(round(cx - crop_w / 2))
                y0 = int(round(cy - crop_h / 2))
                x0 = max(0, min(width - crop_w, x0))
                y0 = max(0, min(height - crop_h, y0))
                yield warped[y0 : y0 + crop_h, x0 : x0 + crop_w]
            else:
                yield warped

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        temp_video = Path(tmp.name)

    frames_written = len(points)
    encode_err = ""
    try:
        ffmpeg = require_ffmpeg()
        ok_encode, encode_err = _encode_with_ffmpeg(
            ffmpeg, frame_generator(), out_w, out_h, fps, temp_video
        )
    except RuntimeError as e:
        cap.release()
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(temp_video), fourcc, fps, (out_w, out_h))
        if not writer.isOpened():
            return {"success": False, "error": "Could not create video writer — install FFmpeg"}
        _seek_capture(cap, start_sec, start_frame)
        written = 0
        for pi, pt in enumerate(points):
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            dx, dy = dx_list[pi], dy_list[pi]
            m = np.float32([[1, 0, dx], [0, 1, dy]])
            warped = cv2.warpAffine(frame, m, (width, height), borderMode=cv2.BORDER_REPLICATE)
            if mode == "crop" and crop_w and crop_h:
                cx = pt.x + pt.width / 2 + dx
                cy = pt.y + pt.height / 2 + dy
                x0 = max(0, min(width - crop_w, int(round(cx - crop_w / 2))))
                y0 = max(0, min(height - crop_h, int(round(cy - crop_h / 2))))
                out_frame = warped[y0 : y0 + crop_h, x0 : x0 + crop_w]
            else:
                out_frame = warped
            writer.write(out_frame)
            written += 1
        writer.release()
        frames_written = written
        ok_encode = written > 0 and temp_video.stat().st_size > 0
        encode_err = str(e)
    finally:
        cap.release()

    if not ok_encode or frames_written == 0:
        temp_video.unlink(missing_ok=True)
        return {"success": False, "error": encode_err or "Video encode failed"}

    video_only = out.with_suffix(".video-only.mp4")
    try:
        ffmpeg = require_ffmpeg()
        mux_ok, mux_err = _mux_audio(ffmpeg, temp_video, path, out, start_sec)
        if not mux_ok:
            import shutil

            shutil.copy2(temp_video, out)
            temp_video.unlink(missing_ok=True)
            return {
                "success": True,
                "output_path": str(out),
                "frames_written": frames_written,
                "frame_count": len(points),
                "method": "tracking_warp",
                "mode": mode,
                "tracker_type": tracker_type,
                "smoothing": smoothing,
                "warning": f"Saved without audio: {mux_err or 'mux failed'}",
            }
    except RuntimeError:
        import shutil

        shutil.copy2(temp_video, out)
        temp_video.unlink(missing_ok=True)
        return {
            "success": True,
            "output_path": str(out),
            "frames_written": frames_written,
            "frame_count": len(points),
            "method": "tracking_warp",
            "mode": mode,
            "warning": "Saved video without audio (FFmpeg not available)",
        }

    temp_video.unlink(missing_ok=True)
    return {
        "success": True,
        "output_path": str(out),
        "frames_written": frames_written,
        "frame_count": len(points),
        "method": "tracking_warp",
        "mode": mode,
        "tracker_type": tracker_type,
        "smoothing": smoothing,
    }
