"""
Cross-platform FFmpeg / FFprobe resolution.

Priority:
  1. AIVE_FFMPEG_PATH / AIVE_FFPROBE_PATH environment variables
  2. config/app.yaml → ffmpeg.ffmpeg_path / ffprobe_path
  3. imageio-ffmpeg bundled binary (pip install imageio-ffmpeg) — no Homebrew needed
  4. vendor/ffmpeg/<platform>/ in project tree (optional manual drop-in)
  5. System PATH (where ffmpeg / ffprobe)

Author: Mohit M
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _config_paths() -> tuple[str | None, str | None]:
    try:
        import yaml

        cfg_path = _PROJECT_ROOT / "config" / "app.yaml"
        if not cfg_path.exists():
            return None, None
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        ff = data.get("ffmpeg") or {}
        return ff.get("ffmpeg_path"), ff.get("ffprobe_path")
    except Exception:
        return None, None


def _vendor_dir() -> Path:
    system = sys.platform
    machine = platform.machine().lower()
    if system == "darwin":
        key = "macos-arm64" if machine in ("arm64", "aarch64") else "macos-x64"
    elif system == "win32":
        key = "win64"
    else:
        key = "linux-x64"
    return _PROJECT_ROOT / "vendor" / "ffmpeg" / key


def _valid_exe(path: str | Path | None) -> str | None:
    if not path:
        return None
    p = Path(path).expanduser()
    if p.is_file() and os.access(p, os.X_OK):
        return str(p.resolve())
    if p.is_file() and sys.platform == "win32" and p.suffix.lower() == ".exe":
        return str(p.resolve())
    return None


def _imageio_ffmpeg() -> str | None:
    try:
        import imageio_ffmpeg

        return _valid_exe(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        return None


def _sibling_ffprobe(ffmpeg_path: str) -> str | None:
    parent = Path(ffmpeg_path).parent
    for name in ("ffprobe", "ffprobe.exe"):
        candidate = parent / name
        if candidate.is_file():
            return str(candidate.resolve())
    return None


@lru_cache(maxsize=1)
def get_ffmpeg_exe() -> str | None:
    env = _valid_exe(os.environ.get("AIVE_FFMPEG_PATH"))
    if env:
        return env

    cfg_ff, _ = _config_paths()
    cfg = _valid_exe(cfg_ff)
    if cfg:
        return cfg

    bundled = _imageio_ffmpeg()
    if bundled:
        return bundled

    vendor = _vendor_dir()
    for name in ("ffmpeg", "ffmpeg.exe"):
        found = _valid_exe(vendor / name)
        if found:
            return found

    return shutil.which("ffmpeg")


@lru_cache(maxsize=1)
def get_ffprobe_exe() -> str | None:
    env = _valid_exe(os.environ.get("AIVE_FFPROBE_PATH"))
    if env:
        return env

    _, cfg_fp = _config_paths()
    cfg = _valid_exe(cfg_fp)
    if cfg:
        return cfg

    ffmpeg = get_ffmpeg_exe()
    if ffmpeg:
        sib = _sibling_ffprobe(ffmpeg)
        if sib:
            return sib

    vendor = _vendor_dir()
    for name in ("ffprobe", "ffprobe.exe"):
        found = _valid_exe(vendor / name)
        if found:
            return found

    return shutil.which("ffprobe")


def ffmpeg_available() -> bool:
    return get_ffmpeg_exe() is not None


def ffprobe_available() -> bool:
    return get_ffprobe_exe() is not None


def media_tools_status() -> dict[str, Any]:
    ff = get_ffmpeg_exe()
    fp = get_ffprobe_exe()
    source = "unknown"
    if os.environ.get("AIVE_FFMPEG_PATH"):
        source = "environment"
    elif _imageio_ffmpeg() and ff == _imageio_ffmpeg():
        source = "imageio-ffmpeg (pip)"
    elif ff and "vendor" in ff:
        source = "vendor/"
    elif ff:
        source = "PATH"

    return {
        "ffmpeg": ff is not None,
        "ffprobe": fp is not None,
        "ffmpeg_path": ff,
        "ffprobe_path": fp,
        "source": source,
        "platform": sys.platform,
        "machine": platform.machine(),
    }


def require_ffmpeg() -> str:
    exe = get_ffmpeg_exe()
    if not exe:
        raise RuntimeError(
            "FFmpeg not found. Easiest fix (all platforms):\n"
            "  pip install imageio-ffmpeg\n"
            "Or set AIVE_FFMPEG_PATH to your ffmpeg binary.\n"
            "See docs/FFMPEG-CROSS-PLATFORM.md"
        )
    return exe


def run_ffmpeg(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
    cmd = [require_ffmpeg(), *args]
    return subprocess.run(cmd, **kwargs)


def run_ffprobe(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
    fp = get_ffprobe_exe()
    if not fp:
        raise RuntimeError("ffprobe not found; install FFmpeg or set AIVE_FFPROBE_PATH")
    cmd = [fp, *args]
    return subprocess.run(cmd, **kwargs)
