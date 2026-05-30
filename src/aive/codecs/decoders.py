"""Video decoders — FFmpeg primary; Windows APIs via adapters."""

from __future__ import annotations

import json
import subprocess
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any

from aive.codecs.ffmpeg_bin import get_ffmpeg_exe, get_ffprobe_exe


class DecoderBackend(str, Enum):
    FFMPEG = "ffmpeg"
    DIRECTSHOW = "directshow"
    VFW = "vfw"
    QUICKTIME = "quicktime"


class VideoDecoder(ABC):
    @abstractmethod
    def probe(self, path: Path) -> dict[str, Any]:
        ...

    @abstractmethod
    def extract_frame(self, path: Path, time_sec: float) -> bytes | None:
        ...


class FFmpegDecoder(VideoDecoder):
    def __init__(self, ffmpeg: str | None = None, ffprobe: str | None = None) -> None:
        self.ffmpeg = ffmpeg or get_ffmpeg_exe() or "ffmpeg"
        self.ffprobe = ffprobe or get_ffprobe_exe() or "ffprobe"

    def _run(self, cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(cmd, capture_output=True, text=True, check=False)

    def probe(self, path: Path) -> dict[str, Any]:
        if not get_ffprobe_exe() and not Path(self.ffprobe).is_file():
            return {"error": "ffprobe not found", "path": str(path)}
        r = self._run(
            [
                self.ffprobe,
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(path),
            ]
        )
        if r.returncode != 0:
            return {"error": r.stderr, "path": str(path)}
        return json.loads(r.stdout)

    def extract_frame(self, path: Path, time_sec: float) -> bytes | None:
        if not get_ffmpeg_exe():
            return None
        cmd = [
            self.ffmpeg,
            "-ss",
            str(time_sec),
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-f",
            "image2pipe",
            "-vcodec",
            "png",
            "-",
        ]
        r = subprocess.run(cmd, capture_output=True)
        return r.stdout if r.returncode == 0 else None


class DirectShowDecoder(VideoDecoder):
    """Windows DirectShow adapter (requires pywin32 + native bridge on Windows)."""

    def probe(self, path: Path) -> dict[str, Any]:
        return {
            "backend": DecoderBackend.DIRECTSHOW.value,
            "path": str(path),
            "note": "Use FFmpeg fallback if DirectShow bridge unavailable",
        }

    def extract_frame(self, path: Path, time_sec: float) -> bytes | None:
        return FFmpegDecoder().extract_frame(path, time_sec)


class VideoForWindowsDecoder(VideoDecoder):
    def probe(self, path: Path) -> dict[str, Any]:
        return {"backend": DecoderBackend.VFW.value, "path": str(path)}

    def extract_frame(self, path: Path, time_sec: float) -> bytes | None:
        return FFmpegDecoder().extract_frame(path, time_sec)


class QuickTimeDecoder(VideoDecoder):
    def probe(self, path: Path) -> dict[str, Any]:
        return {"backend": DecoderBackend.QUICKTIME.value, "path": str(path)}

    def extract_frame(self, path: Path, time_sec: float) -> bytes | None:
        return FFmpegDecoder().extract_frame(path, time_sec)


def get_decoder(backend: DecoderBackend | str = DecoderBackend.FFMPEG) -> VideoDecoder:
    b = DecoderBackend(backend) if isinstance(backend, str) else backend
    return {
        DecoderBackend.FFMPEG: FFmpegDecoder,
        DecoderBackend.DIRECTSHOW: DirectShowDecoder,
        DecoderBackend.VFW: VideoForWindowsDecoder,
        DecoderBackend.QUICKTIME: QuickTimeDecoder,
    }[b]()
