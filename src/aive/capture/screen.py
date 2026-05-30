"""Screen capture via FFmpeg (cross-platform)."""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from aive.codecs.ffmpeg_bin import get_ffmpeg_exe


def capture_screen(output_path: Path, duration_sec: float = 5.0, fps: float = 15.0) -> dict[str, Any]:
    ff = get_ffmpeg_exe()
    if not ff:
        return {"success": False, "error": "FFmpeg required for screen capture"}

    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    system = sys.platform
    cmd: list[str] = [ff, "-y"]

    if system == "darwin":
        cmd += [
            "-f", "avfoundation",
            "-framerate", str(fps),
            "-i", "1:none",
            "-t", str(duration_sec),
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
    elif system == "win32":
        cmd += [
            "-f", "gdigrab",
            "-framerate", str(fps),
            "-i", "desktop",
            "-t", str(duration_sec),
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
    else:
        display = ":0.0"
        cmd += [
            "-f", "x11grab",
            "-framerate", str(fps),
            "-i", display,
            "-t", str(duration_sec),
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=int(duration_sec) + 30)
        if proc.returncode != 0:
            return {"success": False, "error": proc.stderr[-500:] or "Screen capture failed"}
        return {"success": True, "path": str(output_path), "duration_sec": duration_sec, "platform": platform.system()}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Screen capture timed out"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
