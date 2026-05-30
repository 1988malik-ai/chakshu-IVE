"""
Audio redaction — mute regions, volume adjust.

Author: Mohit M
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from aive.codecs.ffmpeg_bin import require_ffmpeg


def redact_audio_regions(
    input_path: Path,
    output_path: Path,
    mute_regions: list[tuple[float, float]],
) -> dict[str, Any]:
    """Mute audio between start/end seconds for each region."""
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    filters = []
    for i, (start, end) in enumerate(mute_regions):
        filters.append(f"volume=enable='between(t,{start},{end})':volume=0")
    af = ",".join(filters) if filters else "anull"
    cmd = [ffmpeg, "-y", "-i", str(input_path), "-af", af, str(output_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {"success": r.returncode == 0, "regions": mute_regions, "stderr": r.stderr[-500:]}


def adjust_volume(input_path: Path, output_path: Path, volume: float = 1.0) -> dict[str, Any]:
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    cmd = [ffmpeg, "-y", "-i", str(input_path), "-af", f"volume={volume}", str(output_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {"success": r.returncode == 0}
