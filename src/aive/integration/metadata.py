"""
External metadata integration via FFprobe / EXIF.

Author: Mohit M
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from aive.codecs.ffmpeg_bin import get_ffprobe_exe


def ffprobe_full(path: Path) -> dict[str, Any]:
    ffprobe = get_ffprobe_exe()
    if not ffprobe:
        return {"error": "ffprobe not found (optional; pip install imageio-ffmpeg for ffmpeg)"}
    r = subprocess.run(
        [
            ffprobe, "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", "-show_chapters", str(path),
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return {"error": r.stderr}
    return json.loads(r.stdout)


def image_exif(path: Path) -> dict[str, Any]:
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        img = Image.open(path)
        exif = img.getexif()
        if not exif:
            return {}
        return {TAGS.get(k, k): str(v) for k, v in exif.items()}
    except Exception as e:
        return {"error": str(e)}


def export_metadata_bundle(path: Path, output_json: Path) -> dict[str, Any]:
    data: dict[str, Any] = {"path": str(path)}
    if path.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".ts", ".mxf"}:
        data["ffprobe"] = ffprobe_full(path)
    else:
        data["exif"] = image_exif(path)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"success": True, "output": str(output_json), "keys": list(data.keys())}
