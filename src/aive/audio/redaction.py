"""
Audio redaction — mute or attenuate time regions (R-114).

Author: Mohit M
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from aive.codecs.ffmpeg_bin import require_ffmpeg


def _normalize_regions(mute_regions: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for start, end in mute_regions:
        s, e = float(start), float(end)
        if e <= s:
            continue
        out.append((max(0.0, s), e))
    return sorted(out, key=lambda x: x[0])


def _mute_filter_expr(regions: list[tuple[float, float]]) -> str:
    if not regions:
        return "anull"
    if len(regions) == 1:
        s, e = regions[0]
        return f"volume=enable='between(t,{s},{e})':volume=0"
    cond = "+".join(f"between(t,{s},{e})" for s, e in regions)
    return f"volume='if({cond},0,1)'"


def _is_video_output(output_path: Path, input_path: Path) -> bool:
    ext = output_path.suffix.lower()
    if ext in {".mp4", ".mov", ".mkv", ".m4v", ".avi"}:
        return True
    if ext in {".aac", ".wav", ".mp3", ".m4a", ".flac"}:
        return False
    return input_path.suffix.lower() in {".mp4", ".mov", ".mkv", ".m4v", ".avi"}


def redact_audio_regions(
    input_path: Path,
    output_path: Path,
    mute_regions: list[tuple[float, float]],
    *,
    mode: str = "mute",
) -> dict[str, Any]:
    """Mute audio between start/end seconds for each region; export audio or video."""
    regions = _normalize_regions(mute_regions)
    if not regions:
        return {"success": False, "error": "No valid mute regions (end must be > start)"}

    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}

    output_path = output_path.expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    af = _mute_filter_expr(regions)
    video_out = _is_video_output(output_path, input_path)

    if video_out:
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(input_path),
            "-af",
            af,
            "-c:v",
            "copy",
            "-map",
            "0:v:0?",
            "-map",
            "0:a:0?",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(output_path),
        ]
    else:
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-af",
            af,
            "-c:a",
            "aac",
            str(output_path),
        ]

    r = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": r.returncode == 0,
        "output": str(output_path),
        "regions": [{"start": s, "end": e} for s, e in regions],
        "region_count": len(regions),
        "mode": mode,
        "video_output": video_out,
        "stderr": (r.stderr or "")[-800:],
    }


def adjust_volume(input_path: Path, output_path: Path, volume: float = 1.0) -> dict[str, Any]:
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    cmd = [ffmpeg, "-y", "-i", str(input_path), "-af", f"volume={volume}", str(output_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {"success": r.returncode == 0, "output": str(output_path), "stderr": (r.stderr or "")[-500:]}
