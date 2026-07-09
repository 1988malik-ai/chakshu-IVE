"""Media format diagnostics for UI and compliance checks."""

from __future__ import annotations

import importlib.util
import sys
from typing import Any

from aive.codecs.ffmpeg_bin import media_tools_status
from aive.imaging import HAS_CV2, HAS_HEIF, HEIF_EXTENSIONS
from aive.media.loader import IMAGE_EXTENSIONS, RAW_EXTENSIONS, VIDEO_EXTENSIONS


STANDARD_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp", ".gif"}
SYSTEM_CODEC_HINTS = {
    "darwin": ["AVFoundation/QuickTime fallback through FFmpeg or system-installed codecs"],
    "win32": ["DirectShow / Media Foundation when exposed through FFmpeg"],
    "linux": ["FFmpeg/GStreamer packages available on PATH"],
}


def media_format_capabilities() -> dict[str, Any]:
    """Summarize image/video/RAW capability and missing dependency guidance."""
    ffmpeg = media_tools_status()
    rawpy_available = importlib.util.find_spec("rawpy") is not None
    platform_hints = SYSTEM_CODEC_HINTS.get(sys.platform, ["FFmpeg/system codecs on PATH"])
    raw_status = "available" if rawpy_available else "dependency_missing"
    heif_status = "available" if HAS_HEIF else "dependency_missing"

    return {
        "standard_images": sorted(STANDARD_IMAGE_EXTENSIONS),
        "specialized_images": sorted((IMAGE_EXTENSIONS - STANDARD_IMAGE_EXTENSIONS) | RAW_EXTENSIONS),
        "raw": {
            "status": raw_status,
            "available": rawpy_available,
            "extensions": sorted(RAW_EXTENSIONS),
            "dependency": "rawpy",
            "install": "pip install rawpy",
        },
        "heif": {
            "status": heif_status,
            "available": HAS_HEIF,
            "extensions": sorted(HEIF_EXTENSIONS),
            "dependency": "pillow-heif",
            "install": "pip install pillow-heif",
        },
        "video": {
            "extensions": sorted(VIDEO_EXTENSIONS),
            "ffmpeg": ffmpeg,
            "opencv_available": HAS_CV2,
            "system_codec_extension": {
                "supported": ffmpeg.get("ffmpeg") is True,
                "source": ffmpeg.get("source", "unknown"),
                "hints": platform_hints,
            },
        },
        "diagnostics": [
            "Use FFmpeg from AIVE_FFMPEG_PATH, bundled/vendor, imageio-ffmpeg, or PATH.",
            "RAW images require rawpy; unsupported RAW files remain loadable as evidence metadata with a clear warning.",
            "HEIC/HEIF requires pillow-heif and is decoded through the imaging loader.",
        ],
    }
