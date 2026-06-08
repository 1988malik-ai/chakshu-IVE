"""Media duration probing for A/V sync and padding (R-117)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from aive.codecs.ffmpeg_bin import get_ffprobe_exe

PAD_THRESHOLD_SEC = 0.08


def probe_duration_sec(path: Path) -> float | None:
    """Container duration in seconds via ffprobe."""
    ffprobe = get_ffprobe_exe()
    if not ffprobe or not path.exists():
        return None
    r = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout or "{}")
        raw = data.get("format", {}).get("duration")
        return float(raw) if raw is not None else None
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def compare_av_duration(video_path: Path, audio_path: Path) -> dict:
    video_dur = probe_duration_sec(video_path)
    audio_dur = probe_duration_sec(audio_path)
    pad_sec = 0.0
    policy = "match"
    if video_dur is not None and audio_dur is not None:
        delta = audio_dur - video_dur
        if delta > PAD_THRESHOLD_SEC:
            pad_sec = delta
            policy = "pad_video"
        elif delta < -PAD_THRESHOLD_SEC:
            policy = "trim_shortest"
        else:
            policy = "match"
    return {
        "video_duration_sec": video_dur,
        "audio_duration_sec": audio_dur,
        "delta_sec": (audio_dur - video_dur) if (video_dur is not None and audio_dur is not None) else None,
        "pad_seconds": round(pad_sec, 3),
        "needs_video_padding": pad_sec > PAD_THRESHOLD_SEC,
        "recommended_policy": policy,
    }
