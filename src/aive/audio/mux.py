"""
Audio mux, sync adjustment, padding — FFmpeg.

Author: Mohit M
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from aive.audio.duration import PAD_THRESHOLD_SEC, compare_av_duration, probe_duration_sec
from aive.codecs.ffmpeg_bin import require_ffmpeg
from aive.export.audio import probe_audio_streams


def _run(cmd: list[str]) -> dict[str, Any]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    out_path = ""
    for i in range(len(cmd) - 1, -1, -1):
        if cmd[i] and not cmd[i].startswith("-") and "." in cmd[i]:
            out_path = cmd[i]
            break
    return {
        "success": r.returncode == 0,
        "output": out_path,
        "command": " ".join(cmd),
        "stderr": r.stderr[-1200:] if r.stderr else "",
    }


def count_audio_streams(video_path: Path) -> int:
    return len(probe_audio_streams(video_path))


def _append_codec_args(cmd: list[str], existing_count: int, new_count: int, audio_codec: str) -> None:
    for i in range(existing_count):
        cmd.extend([f"-c:a:{i}", "copy"])
    for i in range(existing_count, existing_count + new_count):
        codec = audio_codec if audio_codec != "copy" else "aac"
        cmd.extend([f"-c:a:{i}", codec])


def _resolve_padding(
    video_path: Path,
    audio_path: Path,
    *,
    auto_pad_video: bool,
    force_pad: bool,
) -> tuple[bool, float, dict[str, Any]]:
    info = compare_av_duration(video_path, audio_path)
    pad_sec = float(info.get("pad_seconds") or 0)
    if force_pad and pad_sec <= PAD_THRESHOLD_SEC:
        audio_dur = info.get("audio_duration_sec")
        video_dur = info.get("video_duration_sec")
        if audio_dur and video_dur and audio_dur > video_dur:
            pad_sec = audio_dur - video_dur
    apply_pad = (auto_pad_video or force_pad) and pad_sec > PAD_THRESHOLD_SEC
    return apply_pad, pad_sec, info


def add_audio_stream(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    *,
    mode: str = "add",
    audio_codec: str = "aac",
    audio_delay_ms: float = 0,
    use_shortest: bool = False,
    auto_pad_video: bool = True,
    force_pad: bool = False,
    stream_language: str | None = None,
    stream_title: str | None = None,
) -> dict[str, Any]:
    """
    Mux audio onto video.

    mode:
      add — keep ALL existing audio tracks, append new audio as an additional track
      replace — video + new audio only (removes original audio tracks)

    auto_pad_video (R-117): when external audio is longer, extend video with frozen last frame.
    use_shortest: when video is longer than audio, trim output to shortest stream.
    """
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing_audio = count_audio_streams(video_path)
    delay_ms = int(audio_delay_ms)
    keep_existing = mode != "replace"

    apply_pad, pad_sec, dur_info = _resolve_padding(
        video_path,
        audio_path,
        auto_pad_video=auto_pad_video,
        force_pad=force_pad,
    )

    cmd: list[str] = [ffmpeg, "-y", "-i", str(video_path), "-i", str(audio_path)]
    filters: list[str] = []

    if delay_ms:
        filters.append(f"[1:a]adelay={delay_ms}|{delay_ms}[newa]")
        new_audio_ref = "[newa]"
    else:
        new_audio_ref = "1:a:0"

    if apply_pad:
        filters.append(f"[0:v]tpad=stop_mode=clone:stop_duration={pad_sec:.3f}[vpadded]")
        video_ref = "[vpadded]"
    else:
        video_ref = "0:v:0"

    if filters:
        cmd.extend(["-filter_complex", ";".join(filters)])

    cmd.extend(["-map", video_ref])

    if keep_existing:
        cmd.extend(["-map", "0:a?"])
    if delay_ms:
        cmd.extend(["-map", new_audio_ref])
    else:
        cmd.extend(["-map", "1:a:0"])

    if apply_pad:
        cmd.extend(["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p"])
    else:
        cmd.extend(["-c:v", "copy"])

    if keep_existing and existing_audio > 0:
        _append_codec_args(cmd, existing_audio, 1, audio_codec)
    else:
        if audio_codec == "copy":
            cmd.extend(["-c:a", "copy"])
        else:
            cmd.extend(["-c:a", audio_codec])

    trim_shortest = use_shortest and not apply_pad
    if trim_shortest:
        cmd.append("-shortest")

    cmd.append(str(output_path))

    new_idx = existing_audio if keep_existing else 0
    if stream_language:
        cmd.extend([f"-metadata:s:a:{new_idx}", f"language={stream_language}"])
    if stream_title:
        cmd.extend([f"-metadata:s:a:{new_idx}", f"title={stream_title}"])

    result = _run(cmd)
    result["output"] = str(output_path)
    result["mode"] = "add" if keep_existing else "replace"
    result["kept_existing_audio"] = keep_existing
    result["existing_audio_streams"] = existing_audio
    result["audio_streams_after"] = (existing_audio + 1) if keep_existing else 1
    result["duration"] = dur_info
    result["video_padded"] = apply_pad
    result["pad_seconds"] = round(pad_sec, 3) if apply_pad else 0
    result["trimmed_to_shortest"] = trim_shortest
    return result


def pad_video_to_audio_length(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    *,
    keep_original_audio: bool = True,
    audio_codec: str = "aac",
) -> dict[str, Any]:
    """R-117 — extend video to match longer audio (freeze last frame)."""
    return add_audio_stream(
        video_path,
        audio_path,
        output_path,
        mode="add" if keep_original_audio else "replace",
        audio_codec=audio_codec,
        auto_pad_video=True,
        force_pad=True,
        use_shortest=False,
    )


def add_multiple_audio_streams(
    video_path: Path,
    audio_paths: list[Path],
    output_path: Path,
    *,
    keep_original: bool = True,
    audio_codec: str = "aac",
    use_shortest: bool = False,
    auto_pad_video: bool = True,
) -> dict[str, Any]:
    if not audio_paths:
        return {"success": False, "error": "No audio paths provided"}
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing_audio = count_audio_streams(video_path) if keep_original else 0

    longest_audio = max((probe_duration_sec(p) or 0) for p in audio_paths)
    video_dur = probe_duration_sec(video_path) or 0
    pad_sec = max(0.0, longest_audio - video_dur)
    apply_pad = auto_pad_video and pad_sec > PAD_THRESHOLD_SEC

    cmd: list[str] = [ffmpeg, "-y", "-i", str(video_path)]
    for ap in audio_paths:
        cmd.extend(["-i", str(ap)])

    if apply_pad:
        cmd.extend(
            [
                "-filter_complex",
                f"[0:v]tpad=stop_mode=clone:stop_duration={pad_sec:.3f}[vpadded]",
                "-map",
                "[vpadded]",
            ]
        )
        cmd.extend(["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p"])
    else:
        cmd.extend(["-map", "0:v:0", "-c:v", "copy"])

    if keep_original:
        cmd.extend(["-map", "0:a?"])
    for i in range(len(audio_paths)):
        cmd.extend(["-map", f"{i + 1}:a:0"])

    _append_codec_args(cmd, existing_audio, len(audio_paths), audio_codec)
    if use_shortest and not apply_pad:
        cmd.append("-shortest")
    cmd.append(str(output_path))

    result = _run(cmd)
    result["output"] = str(output_path)
    result["tracks_added"] = len(audio_paths)
    result["kept_existing_audio"] = keep_original
    result["audio_streams_after"] = existing_audio + len(audio_paths)
    result["video_padded"] = apply_pad
    result["pad_seconds"] = round(pad_sec, 3) if apply_pad else 0
    return result


def adjust_av_sync(video_path: Path, output_path: Path, audio_delay_ms: float = 0) -> dict[str, Any]:
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    delay_sec = audio_delay_ms / 1000.0
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video_path),
        "-itsoffset",
        str(delay_sec),
        "-i",
        str(video_path),
        "-map",
        "0:v",
        "-map",
        "1:a",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        str(output_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {"success": r.returncode == 0, "delay_ms": audio_delay_ms, "stderr": r.stderr[-500:]}


def merge_videos_concat(list_file: Path, output_path: Path) -> dict[str, Any]:
    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(output_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {"success": r.returncode == 0, "stderr": r.stderr[-500:]}
