"""R-173 — merge A/V streams and concatenate videos."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

from aive.codecs.ffmpeg_bin import require_ffmpeg


def _run(cmd: list[str]) -> dict[str, Any]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": r.returncode == 0,
        "command": " ".join(cmd),
        "stderr": r.stderr[-1200:] if r.stderr else "",
    }


def merge_av_streams(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    audio_delay_ms: float = 0.0,
) -> dict[str, Any]:
    """Mux external audio onto video (replace default audio track)."""
    from aive.audio.mux import add_audio_stream

    return add_audio_stream(
        video_path,
        audio_path,
        output_path,
        mode="replace",
        audio_codec="aac",
        audio_delay_ms=audio_delay_ms,
        use_shortest=False,
        auto_pad_video=True,
    )


def concat_videos(
    paths: list[Path],
    output_path: Path,
    reencode: bool = True,
) -> dict[str, Any]:
    """Sequential multi-video merge."""
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    if len(paths) < 2:
        return {"success": False, "error": "At least two video paths required"}

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
        for p in paths:
            escaped = str(p).replace("'", "'\\''")
            tf.write(f"file '{escaped}'\n")
        list_path = tf.name

    cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", list_path]
    if reencode:
        cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"])
    else:
        cmd.extend(["-c", "copy"])
    cmd.append(str(output_path))
    result = _run(cmd)
    Path(list_path).unlink(missing_ok=True)
    result["segment_count"] = len(paths)
    return result
