"""
Frame-accurate audio sync and multichannel probe.

Author: Mohit M
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from aive.codecs.ffmpeg_bin import get_ffprobe_exe, require_ffmpeg
from aive.export.audio import probe_audio_streams


def probe_multichannel(path: Path) -> dict[str, Any]:
    streams = probe_audio_streams(path)
    layout = []
    for s in streams:
        ch = s.get("channels") or 0
        layout.append(
            {
                **s,
                "layout": _channel_layout(ch),
                "multichannel": (ch or 0) > 2,
            }
        )
    return {
        "path": str(path),
        "stream_count": len(layout),
        "streams": layout,
        "has_multichannel": any(x.get("multichannel") for x in layout),
    }


def _channel_layout(channels: int) -> str:
    return {
        1: "mono",
        2: "stereo",
        6: "5.1",
        8: "7.1",
    }.get(channels, f"{channels}ch")


def audio_time_for_frame(
    path: Path,
    frame_index: int,
    fps: float | None,
    pts_sec: float | None = None,
) -> dict[str, Any]:
    """Map video frame to audio timeline (VFR uses pts when available)."""
    if pts_sec is not None:
        t = pts_sec
        mode = "vfr_pts"
    elif fps and fps > 0:
        t = frame_index / fps
        mode = "cfr_fps"
    else:
        return {"error": "Need pts_sec or fps for audio sync"}
    return {
        "path": str(path),
        "frame_index": frame_index,
        "audio_time_sec": t,
        "sync_mode": mode,
    }


def extract_audio_clip(
    path: Path,
    output_path: Path,
    start_sec: float,
    duration_sec: float = 0.04,
) -> dict[str, Any]:
    """Short audio slice around a frame (forensic audition)."""
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    cmd = [
        ffmpeg, "-y",
        "-ss", str(max(0, start_sec)),
        "-i", str(path),
        "-t", str(duration_sec),
        "-vn",
        "-acodec", "pcm_s16le",
        str(output_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": r.returncode == 0,
        "output": str(output_path),
        "start_sec": start_sec,
        "duration_sec": duration_sec,
    }


def stream_sync_offset(path: Path) -> dict[str, Any]:
    """Estimate A/V start offset via ffprobe stream start_time."""
    ffprobe = get_ffprobe_exe()
    if not ffprobe:
        return {"error": "ffprobe required for stream sync analysis"}
    r = subprocess.run(
        [
            ffprobe, "-v", "quiet", "-print_format", "json",
            "-show_streams", str(path),
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return {"error": r.stderr}
    streams = json.loads(r.stdout).get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if not video or not audio:
        return {"error": "Need both video and audio streams"}
    v_start = float(video.get("start_time") or 0)
    a_start = float(audio.get("start_time") or 0)
    return {
        "video_start_sec": v_start,
        "audio_start_sec": a_start,
        "offset_sec": a_start - v_start,
        "recommendation_ms": round((a_start - v_start) * 1000, 2),
    }
