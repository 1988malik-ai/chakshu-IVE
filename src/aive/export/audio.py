"""Audio stream extraction and metadata via FFmpeg."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from aive.codecs.ffmpeg_bin import get_ffprobe_exe, require_ffmpeg


def extract_audio(
    input_path: Path,
    output_path: Path,
    codec: str = "copy",
    format_hint: str | None = None,
) -> dict[str, Any]:
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}

    out = output_path
    if format_hint and not out.suffix:
        out = out.with_suffix(f".{format_hint}")

    cmd = [ffmpeg, "-y", "-i", str(input_path), "-vn"]
    if codec == "copy":
        cmd.extend(["-acodec", "copy", str(out)])
    else:
        cmd.extend(["-acodec", codec, str(out)])

    r = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": r.returncode == 0,
        "output": str(out),
        "stderr": r.stderr[-500:] if r.stderr else "",
    }


def probe_audio_streams(input_path: Path) -> list[dict[str, Any]]:
    ffprobe = get_ffprobe_exe()
    if not ffprobe:
        return []
    r = subprocess.run(
        [
            ffprobe, "-v", "quiet", "-print_format", "json",
            "-show_streams", "-select_streams", "a", str(input_path),
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return []
    streams = json.loads(r.stdout).get("streams", [])
    return [
        {
            "index": s.get("index"),
            "codec": s.get("codec_name"),
            "channels": s.get("channels"),
            "sample_rate": s.get("sample_rate"),
            "bitrate": s.get("bit_rate"),
            "language": s.get("tags", {}).get("language"),
        }
        for s in streams
    ]
