"""
Advanced seek — frames, time, I-frames.

Author: Mohit M
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from aive.analysis.stream import StreamAnalyzer
from aive.codecs.ffmpeg_bin import get_ffmpeg_exe
from aive.imaging import HAS_CV2, bgr_from_bytes

if HAS_CV2:
    import cv2


def extract_frame_at_time(path: Path, time_sec: float) -> dict[str, Any]:
    ffmpeg = get_ffmpeg_exe()
    if ffmpeg:
        cmd = [
            ffmpeg, "-y", "-ss", str(time_sec), "-i", str(path),
            "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-",
        ]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0 and r.stdout:
            frame = bgr_from_bytes(r.stdout, path.name)
            from aive.imaging import bgr_to_jpeg_base64

            return {
                "success": True,
                "time_sec": time_sec,
                "preview": bgr_to_jpeg_base64(frame),
                "width": frame.shape[1],
                "height": frame.shape[0],
            }
    if HAS_CV2:
        cap = cv2.VideoCapture(str(path))
        cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000)
        ok, frame = cap.read()
        cap.release()
        if ok:
            from aive.imaging import bgr_to_jpeg_base64

            return {"success": True, "time_sec": time_sec, "preview": bgr_to_jpeg_base64(frame)}
    return {"success": False, "error": "Could not extract frame"}


def extract_frame_at_index(path: Path, frame_index: int) -> dict[str, Any]:
    if not HAS_CV2:
        return {"success": False, "error": "OpenCV required for frame index seek"}
    cap = cv2.VideoCapture(str(path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return {"success": False, "error": "Frame index out of range"}
    from aive.imaging import bgr_to_jpeg_base64

    return {
        "success": True,
        "frame_index": frame_index,
        "preview": bgr_to_jpeg_base64(frame),
        "fps": cap.get(cv2.CAP_PROP_FPS) if cap else None,
    }


def extract_iframe_near(path: Path, time_sec: float) -> dict[str, Any]:
    analyzer = StreamAnalyzer()
    frames = analyzer.analyze_frame_types(path)
    i_frames = [f for f in frames if f.frame_type == "I" and f.pts <= time_sec]
    if not i_frames:
        i_frames = [f for f in frames if f.frame_type == "I"]
    if not i_frames:
        return extract_frame_at_time(path, time_sec)
    target = max(i_frames, key=lambda f: f.pts)
    result = extract_frame_at_time(path, target.pts)
    result["iframe_pts"] = target.pts
    result["iframe_index"] = target.index
    return result


def get_video_info(path: Path) -> dict[str, Any]:
    analyzer = StreamAnalyzer()
    streams = analyzer.probe_streams(path)
    summary = analyzer.frame_type_summary(path)
    fps = streams[0].fps if streams else None
    duration = streams[0].duration if streams else None
    frame_count = None
    if HAS_CV2:
        cap = cv2.VideoCapture(str(path))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
    return {
        "path": str(path),
        "streams": [s.__dict__ for s in streams],
        "frame_types": summary,
        "fps": fps,
        "duration": duration,
        "frame_count": frame_count,
    }
