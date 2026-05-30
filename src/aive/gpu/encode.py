"""GPU-accelerated H.264 / H.265 encoding via FFmpeg."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from enum import Enum

from aive.codecs.ffmpeg_bin import get_ffmpeg_exe


class GpuVendor(str, Enum):
    NVIDIA = "nvidia"
    INTEL = "intel"
    AMD = "amd"
    CPU = "cpu"


@dataclass
class GpuEncoder:
    name: str
    codec_h264: str
    codec_h265: str
    vendor: GpuVendor


ENCODERS = [
    GpuEncoder("NVIDIA NVENC", "h264_nvenc", "hevc_nvenc", GpuVendor.NVIDIA),
    GpuEncoder("Intel Quick Sync", "h264_qsv", "hevc_qsv", GpuVendor.INTEL),
    GpuEncoder("AMD AMF", "h264_amf", "hevc_amf", GpuVendor.AMD),
    GpuEncoder("CPU (libx264/libx265)", "libx264", "libx265", GpuVendor.CPU),
]


def detect_available_encoders(ffmpeg: str | None = None) -> list[GpuEncoder]:
    ffmpeg = ffmpeg or get_ffmpeg_exe() or "ffmpeg"
    if not get_ffmpeg_exe():
        return [ENCODERS[-1]]
    r = subprocess.run(
        [ffmpeg, "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
    )
    out = r.stdout + r.stderr
    available = []
    for enc in ENCODERS:
        if enc.codec_h264 in out or enc.codec_h265 in out:
            available.append(enc)
    return available or [ENCODERS[-1]]


def select_encoder(
    prefer_h265: bool = False,
    priority: list[str] | None = None,
) -> tuple[str, GpuVendor]:
    priority = priority or ["nvenc", "qsv", "amf", "cpu"]
    available = detect_available_encoders()
    for key in priority:
        for enc in available:
            if key == "cpu" and enc.vendor == GpuVendor.CPU:
                return (enc.codec_h265 if prefer_h265 else enc.codec_h264, enc.vendor)
            if key == "nvenc" and enc.vendor == GpuVendor.NVIDIA:
                return (enc.codec_h265 if prefer_h265 else enc.codec_h264, enc.vendor)
            if key == "qsv" and enc.vendor == GpuVendor.INTEL:
                return (enc.codec_h265 if prefer_h265 else enc.codec_h264, enc.vendor)
            if key == "amf" and enc.vendor == GpuVendor.AMD:
                return (enc.codec_h265 if prefer_h265 else enc.codec_h264, enc.vendor)
    enc = available[0]
    return (enc.codec_h265 if prefer_h265 else enc.codec_h264, enc.vendor)
