"""Build video from image sequences (R-181)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from aive.codecs.ffmpeg_bin import get_ffmpeg_exe


def images_to_video(
    input_dir: str,
    output_path: Path,
    fps: float = 30.0,
    pattern: str = "*.jpg",
) -> dict[str, Any]:
    ff = get_ffmpeg_exe()
    if not ff:
        return {"success": False, "error": "FFmpeg required"}

    src_dir = Path(input_dir).expanduser().resolve()
    if not src_dir.is_dir():
        return {"success": False, "error": f"Not a directory: {src_dir}"}

    files = sorted(src_dir.glob(pattern))
    if not files:
        files = sorted(src_dir.glob("*.png")) + sorted(src_dir.glob("*.jpeg"))
    if not files:
        return {"success": False, "error": "No image frames found"}

    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    list_file = output_path.parent / "_chakshu_frames.txt"
    list_file.write_text(
        "\n".join(f"file '{f.resolve()}'" for f in files) + "\n",
        encoding="utf-8",
    )

    cmd = [
        ff, "-y",
        "-f", "concat", "-safe", "0",
        "-r", str(fps),
        "-i", str(list_file),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        list_file.unlink(missing_ok=True)
        if proc.returncode != 0:
            return {"success": False, "error": proc.stderr[-600:] or "Encode failed"}
        return {"success": True, "path": str(output_path), "frame_count": len(files), "fps": fps}
    except Exception as exc:
        list_file.unlink(missing_ok=True)
        return {"success": False, "error": str(exc)}
