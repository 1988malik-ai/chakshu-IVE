"""Video/image export — CFR/VFR, stream copy, GPU encode."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from aive.codecs.ffmpeg_bin import get_ffmpeg_exe, require_ffmpeg


class FrameRateMode(str, Enum):
    CFR = "cfr"
    VFR = "vfr"


@dataclass
class ExportOptions:
    output_path: Path
    video_codec: str = "libx264"
    audio_codec: str = "copy"
    frame_rate_mode: FrameRateMode = FrameRateMode.CFR
    fps: float | None = 29.97
    use_stream_copy: bool = True
    gpu_encoder: str | None = None  # h264_nvenc, hevc_nvenc, h264_qsv, etc.
    gpu_preset: str = "p4"
    subtitle_path: Path | None = None
    burn_subtitles: bool = False
    faststart: bool = True  # VMS-friendly moov atom
    pixel_format: str = "yuv420p"
    crf: int | None = 23
    video_bitrate: str | None = None  # e.g. "8M"
    encode_preset: str = "medium"  # libx264 / libx265 CPU preset


class VideoExporter:
    def __init__(self, ffmpeg: str | None = None) -> None:
        self.ffmpeg = ffmpeg or get_ffmpeg_exe() or "ffmpeg"

    def build_command(
        self,
        input_path: Path,
        options: ExportOptions,
        filter_complex: str | None = None,
    ) -> list[str]:
        cmd = [self.ffmpeg, "-y", "-i", str(input_path)]

        if options.subtitle_path and options.burn_subtitles:
            cmd.extend(["-i", str(options.subtitle_path)])

        if filter_complex:
            cmd.extend(["-filter_complex", filter_complex])

        video_args: list[str] = []
        if options.use_stream_copy and not filter_complex and not options.burn_subtitles:
            video_args = ["-c:v", "copy"]
        else:
            enc = options.gpu_encoder or options.video_codec
            video_args = ["-c:v", enc]
            if options.gpu_encoder:
                if "nvenc" in enc:
                    video_args.extend(["-preset", options.gpu_preset])
                elif "qsv" in enc:
                    video_args.extend(["-preset", "medium"])
            elif enc in ("libx264", "libx265") and options.encode_preset:
                video_args.extend(["-preset", options.encode_preset])
            if options.crf is not None and enc in ("libx264", "libx265", "libvpx-vp9"):
                video_args.extend(["-crf", str(options.crf)])
            elif options.video_bitrate:
                video_args.extend(["-b:v", options.video_bitrate])
            video_args.extend(["-pix_fmt", options.pixel_format])

        cmd.extend(video_args)

        if options.audio_codec == "copy":
            cmd.extend(["-c:a", "copy"])
        else:
            cmd.extend(["-c:a", options.audio_codec])

        if options.frame_rate_mode == FrameRateMode.CFR and options.fps:
            cmd.extend(["-r", str(options.fps)])
        elif options.frame_rate_mode == FrameRateMode.VFR:
            cmd.extend(["-vsync", "vfr"])

        if options.faststart:
            cmd.extend(["-movflags", "+faststart"])

        cmd.append(str(options.output_path))
        return cmd

    def export(
        self,
        input_path: Path,
        options: ExportOptions,
        filter_complex: str | None = None,
    ) -> dict[str, Any]:
        if not shutil.which(self.ffmpeg):
            return {"success": False, "error": "ffmpeg not found"}
        cmd = self.build_command(input_path, options, filter_complex)
        r = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": r.returncode == 0,
            "command": " ".join(cmd),
            "stderr": r.stderr,
            "output": str(options.output_path),
        }


# Common export presets (standard + extended via system codecs)
EXPORT_PRESETS: dict[str, dict[str, str]] = {
    "mp4_h264": {"ext": ".mp4", "video_codec": "libx264", "audio_codec": "aac"},
    "mp4_h265": {"ext": ".mp4", "video_codec": "libx265", "audio_codec": "aac"},
    "mkv_copy": {"ext": ".mkv", "video_codec": "copy", "audio_codec": "copy"},
    "mov_prores": {"ext": ".mov", "video_codec": "prores_ks", "audio_codec": "pcm_s16le"},
    "avi_uncompressed": {"ext": ".avi", "video_codec": "rawvideo", "audio_codec": "pcm_s16le"},
    "webm_vp9": {"ext": ".webm", "video_codec": "libvpx-vp9", "audio_codec": "libopus"},
    "mxf_mpeg2": {"ext": ".mxf", "video_codec": "mpeg2video", "audio_codec": "pcm_s16le"},
    "ts_h264": {"ext": ".ts", "video_codec": "libx264", "audio_codec": "aac"},
    "wmv": {"ext": ".wmv", "video_codec": "wmv2", "audio_codec": "wmav2"},
    "flv": {"ext": ".flv", "video_codec": "flv", "audio_codec": "mp3"},
}
