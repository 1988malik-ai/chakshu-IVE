#!/usr/bin/env python3
"""Print media dependency status for AI-IVE (run from project root)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aive.codecs.ffmpeg_bin import media_tools_status
from aive.imaging import HAS_CV2


def main() -> int:
    print("=== AI-IVE media dependencies ===\n")
    st = media_tools_status()
    print(f"Platform:     {st['platform']} / {st['machine']}")
    print(f"OpenCV:       {'yes' if HAS_CV2 else 'no (images still work via Pillow)'}")
    print(f"FFmpeg:       {'yes' if st['ffmpeg'] else 'NO'}")
    print(f"  source:     {st['source']}")
    print(f"  path:       {st['ffmpeg_path'] or '—'}")
    print(f"FFprobe:      {'yes' if st['ffprobe'] else 'optional (some probes use ffmpeg only)'}")
    print(f"  path:       {st['ffprobe_path'] or '—'}")

    if not st["ffmpeg"]:
        print("\nFix:")
        print("  source .venv/bin/activate")
        print("  pip install -r requirements-video.txt")
        print("  python scripts/check-media-deps.py")
        return 1

    print("\nVideo features: ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
