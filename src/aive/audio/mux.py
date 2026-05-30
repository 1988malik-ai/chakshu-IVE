"""
Audio mux, sync adjustment, padding — FFmpeg.

Author: Mohit M
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from aive.codecs.ffmpeg_bin import require_ffmpeg


def add_audio_stream(video_path: Path, audio_path: Path, output_path: Path) -> dict[str, Any]:
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    cmd = [
        ffmpeg, "-y", "-i", str(video_path), "-i", str(audio_path),
        "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0", "-shortest", str(output_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {"success": r.returncode == 0, "output": str(output_path), "stderr": r.stderr[-500:]}


def adjust_av_sync(video_path: Path, output_path: Path, audio_delay_ms: float = 0) -> dict[str, Any]:
    """Delay audio relative to video (ms)."""
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    delay_sec = audio_delay_ms / 1000.0
    cmd = [
        ffmpeg, "-y", "-i", str(video_path),
        "-itsoffset", str(delay_sec),
        "-i", str(video_path),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "copy", "-c:a", "aac", str(output_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {"success": r.returncode == 0, "delay_ms": audio_delay_ms, "stderr": r.stderr[-500:]}


def pad_video_to_audio_length(video_path: Path, audio_path: Path, output_path: Path) -> dict[str, Any]:
    """Extend video with last frame if shorter than audio."""
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    cmd = [
        ffmpeg, "-y", "-i", str(video_path), "-i", str(audio_path),
        "-filter_complex", "[0:v]tpad=stop_mode=clone:stop_duration=shortest[v]",
        "-map", "[v]", "-map", "1:a", "-c:a", "copy", str(output_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {"success": r.returncode == 0, "output": str(output_path)}


def merge_videos_concat(list_file: Path, output_path: Path) -> dict[str, Any]:
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(output_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {"success": r.returncode == 0, "stderr": r.stderr[-500:]}
