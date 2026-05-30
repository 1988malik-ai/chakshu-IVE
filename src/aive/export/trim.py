"""
Frame selection and trim without transcoding (stream copy segments).

Author: Mohit M
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from aive.codecs.ffmpeg_bin import get_ffmpeg_exe, require_ffmpeg


def trim_segment_copy(
    input_path: Path,
    output_path: Path,
    start_sec: float,
    end_sec: float,
) -> dict[str, Any]:
    """Extract segment using stream copy where possible."""
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    duration = max(0.01, end_sec - start_sec)
    cmd = [
        ffmpeg, "-y",
        "-ss", str(start_sec),
        "-i", str(input_path),
        "-t", str(duration),
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        str(output_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": r.returncode == 0,
        "output": str(output_path),
        "start_sec": start_sec,
        "end_sec": end_sec,
        "stderr": r.stderr[-800:] if r.stderr else "",
    }


def export_frame_list_copy(
    input_path: Path,
    output_dir: Path,
    frame_indices: list[int],
) -> dict[str, Any]:
    """Export specific frames as images via ffmpeg select filter."""
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    output_dir.mkdir(parents=True, exist_ok=True)
    exported = []
    for idx in frame_indices:
        out = output_dir / f"frame_{idx:06d}.jpg"
        cmd = [
            ffmpeg, "-y", "-i", str(input_path),
            "-vf", f"select=eq(n\\,{idx})",
            "-frames:v", "1", str(out),
        ]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            exported.append(str(out))
    return {"success": bool(exported), "exported": exported, "count": len(exported)}
