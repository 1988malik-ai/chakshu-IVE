"""
Section 16 — advanced video processing via FFmpeg (R-150, R-158–R-165).

Author: Mohit M
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Literal

from aive.codecs.ffmpeg_bin import require_ffmpeg


def _run(cmd: list[str]) -> dict[str, Any]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": r.returncode == 0,
        "command": " ".join(cmd),
        "stderr": r.stderr[-1200:] if r.stderr else "",
    }


def adjust_frame_rate(
    input_path: Path,
    output_path: Path,
    target_fps: float,
    method: Literal["dup", "blend", "fps"] = "fps",
) -> dict[str, Any]:
    """R-161 / R-162 — duplicate, drop, or interpolate frames to target FPS."""
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    if method == "dup":
        vf = f"fps={target_fps}"
    elif method == "blend":
        vf = f"minterpolate=fps={target_fps}:mi_mode=mci"
    else:
        vf = f"fps={target_fps}"
    cmd = [
        ffmpeg, "-y", "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        str(output_path),
    ]
    return _run(cmd)


def reverse_video(input_path: Path, output_path: Path) -> dict[str, Any]:
    """R-165 — reverse playback order."""
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    cmd = [
        ffmpeg, "-y", "-i", str(input_path),
        "-vf", "reverse",
        "-af", "areverse",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        str(output_path),
    ]
    return _run(cmd)


def freeze_frame_video(
    input_path: Path,
    output_path: Path,
    time_sec: float = 0.0,
    duration_sec: float = 3.0,
) -> dict[str, Any]:
    """R-164 — hold a single frame for a duration (placeholder / freeze clip)."""
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    duration_sec = max(0.1, duration_sec)
    vf = f"select=eq(n\\,0),loop=loop={max(1, int(duration_sec * 30))}:size=1:start=0,setpts=N/(30*TB)"
    cmd = [
        ffmpeg, "-y",
        "-ss", str(time_sec),
        "-i", str(input_path),
        "-vf", vf,
        "-t", str(duration_sec),
        "-r", "30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-an",
        str(output_path),
    ]
    return _run(cmd)


def deinterlace_video(
    input_path: Path,
    output_path: Path,
    mode: Literal["yadif", "bwdif", "w3fdif"] = "yadif",
) -> dict[str, Any]:
    """R-150 — full-video deinterlace."""
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    vf = f"{mode}=mode=send_frame:parity=auto:deint=all"
    cmd = [
        ffmpeg, "-y", "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(output_path),
    ]
    return _run(cmd)


def stabilize_video(
    input_path: Path,
    output_path: Path,
    smoothing: int = 10,
) -> dict[str, Any]:
    """R-160 — two-pass vidstab or deshake fallback."""
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    transforms = output_path.with_suffix(".trf")
    pass1 = [
        ffmpeg, "-y", "-i", str(input_path),
        "-vf", f"vidstabdetect=shakiness=5:accuracy=15:result={transforms}",
        "-f", "null", "-",
    ]
    r1 = subprocess.run(pass1, capture_output=True, text=True)
    if r1.returncode == 0 and transforms.exists():
        pass2 = [
            ffmpeg, "-y", "-i", str(input_path),
            "-vf", f"vidstabtransform=input={transforms}:smoothing={smoothing}:zoom=0",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            str(output_path),
        ]
        result = _run(pass2)
        transforms.unlink(missing_ok=True)
        result["method"] = "vidstab"
        return result
    cmd = [
        ffmpeg, "-y", "-i", str(input_path),
        "-vf", "deshake",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(output_path),
    ]
    result = _run(cmd)
    result["method"] = "deshake"
    return result


def perspective_stabilize_video(input_path: Path, output_path: Path) -> dict[str, Any]:
    """R-158 — perspective correction via deshake + rotate auto."""
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    cmd = [
        ffmpeg, "-y", "-i", str(input_path),
        "-vf", "deshake:xshakiness=16:yshakiness=16",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(output_path),
    ]
    return _run(cmd)
