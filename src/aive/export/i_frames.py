"""Selective export of intra-coded (I) frames."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from aive.analysis.stream import StreamAnalyzer


def export_i_frames(
    input_path: Path,
    output_dir: Path,
    image_format: str = "jpg",
    select_all_keyframes: bool = True,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    analyzer = StreamAnalyzer()
    frames = analyzer.analyze_frame_types(input_path)
    i_frames = [f for f in frames if f.frame_type == "I" or (select_all_keyframes and f.key_frame)]

    if not i_frames:
        return {"success": False, "error": "No I-frames found", "exported": 0}

    if not shutil.which("ffmpeg"):
        return {"success": False, "error": "ffmpeg required for I-frame export"}

    exported = []
    for i, finfo in enumerate(i_frames):
        out = output_dir / f"i_frame_{i:05d}_{finfo.pts:.3f}s.{image_format}"
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(finfo.pts),
            "-i", str(input_path),
            "-frames:v", "1",
            "-q:v", "2",
            str(out),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            exported.append({"path": str(out), "pts": finfo.pts, "index": finfo.index})

    return {
        "success": len(exported) > 0,
        "exported": len(exported),
        "total_i_frames": len(i_frames),
        "files": exported,
        "output_dir": str(output_dir),
    }
