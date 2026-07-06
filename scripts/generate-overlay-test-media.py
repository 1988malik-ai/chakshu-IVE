#!/usr/bin/env python3
"""
Generate short sample videos for testing video overlays & side-by-side compare.

Outputs to examples/test-media/:
  primary-left.mp4      — blue scene (primary evidence)
  inset-right.mp4       — green scene (compare / PiP)
  demo-side-by-side.mp4 — example side-by-side output
  demo-pip.mp4          — example PiP output

Run from project root:
  python3 scripts/generate-overlay-test-media.py

Requires OpenCV OR FFmpeg on PATH (brew install ffmpeg / pip install imageio-ffmpeg).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples" / "test-media"
FPS = 15
SEC = 4
W, H = 480, 270


def _ffmpeg() -> str | None:
    try:
        sys.path.insert(0, str(ROOT / "src"))
        from aive.codecs.ffmpeg_bin import get_ffmpeg_exe

        return get_ffmpeg_exe()
    except Exception:
        import shutil

        return shutil.which("ffmpeg")


def _run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "ffmpeg failed")[-500:])


def generate_with_ffmpeg(ffmpeg: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    left = OUT / "primary-left.mp4"
    right = OUT / "inset-right.mp4"
    sbs = OUT / "demo-side-by-side.mp4"
    pip = OUT / "demo-pip.mp4"

    _run([
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"color=c=#2864B4:s={W}x{H}:d={SEC}:r={FPS}",
        "-vf", f"drawtext=text='LEFT PRIMARY':x=20:y=30:fontsize=28:fontcolor=white,"
               f"drawtext=text='t=%{{pts\\:gmtime\\:0\\:%H\\M\\S}}':x=20:y={H-40}:fontsize=20:fontcolor=white",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(left),
    ])
    _run([
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"color=c=#3CA050:s={W}x{H}:d={SEC}:r={FPS}",
        "-vf", f"drawtext=text='RIGHT INSET':x=20:y=30:fontsize=28:fontcolor=white,"
               f"drawtext=text='t=%{{pts\\:gmtime\\:0\\:%H\\M\\S}}':x=20:y={H-40}:fontsize=20:fontcolor=white",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(right),
    ])
    _run([
        ffmpeg, "-y", "-i", str(left), "-i", str(right),
        "-filter_complex", f"[0:v][1:v]hstack=inputs=2[v]",
        "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(sbs),
    ])
    _run([
        ffmpeg, "-y", "-i", str(left), "-i", str(right),
        "-filter_complex",
        f"[1:v]scale=iw*0.28:-1[inset];[0:v][inset]overlay=W-w-10:10[v]",
        "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(pip),
    ])
    for p in (left, right, sbs, pip):
        print(f"Wrote {p} ({p.stat().st_size // 1024} KB)")


def generate_with_opencv() -> None:
    import cv2
    import numpy as np

    sys.path.insert(0, str(ROOT / "src"))
    from aive.overlays.compose import draw_pip, side_by_side

    OUT.mkdir(parents=True, exist_ok=True)
    n = FPS * SEC
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    def write_clip(path: Path, draw_fn) -> None:
        wr = cv2.VideoWriter(str(path), fourcc, FPS, (W, H))
        for i in range(n):
            wr.write(draw_fn(i, n))
        wr.release()

    def draw_left(i: int, total: int):
        t = i / max(total - 1, 1)
        frame = np.full((H, W, 3), (180, 90, 40), np.uint8)
        x = int(40 + t * (W - 120))
        cv2.rectangle(frame, (x, H // 2 - 30), (x + 80, H // 2 + 30), (0, 220, 255), -1)
        cv2.putText(frame, "LEFT PRIMARY", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"t={i/FPS:.1f}s", (20, H - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        return frame

    def draw_right(i: int, total: int):
        t = i / max(total - 1, 1)
        frame = np.full((H, W, 3), (50, 160, 60), np.uint8)
        cx = int(W // 2 + 60 * np.sin(t * 6.28))
        cv2.circle(frame, (cx, H // 2), 45, (0, 255, 180), -1)
        cv2.putText(frame, "RIGHT INSET", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"t={i/FPS:.1f}s", (20, H - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        return frame

    left_path = OUT / "primary-left.mp4"
    right_path = OUT / "inset-right.mp4"
    write_clip(left_path, draw_left)
    write_clip(right_path, draw_right)

    cap_l = cv2.VideoCapture(str(left_path))
    cap_r = cv2.VideoCapture(str(right_path))
    sbs_wr = cv2.VideoWriter(str(OUT / "demo-side-by-side.mp4"), fourcc, FPS, (W * 2, H))
    pip_wr = cv2.VideoWriter(str(OUT / "demo-pip.mp4"), fourcc, FPS, (W, H))
    for _ in range(n):
        ok_l, fl = cap_l.read()
        ok_r, fr = cap_r.read()
        if not ok_l or not ok_r:
            break
        sbs_wr.write(side_by_side(fl, fr))
        pip_wr.write(draw_pip(fl, fr, scale=0.28, position="top-right"))
    cap_l.release()
    cap_r.release()
    sbs_wr.release()
    pip_wr.release()
    for name in ("primary-left.mp4", "inset-right.mp4", "demo-side-by-side.mp4", "demo-pip.mp4"):
        p = OUT / name
        print(f"Wrote {p} ({p.stat().st_size // 1024} KB)")


def main() -> int:
    try:
        import cv2  # noqa: F401

        generate_with_opencv()
    except ImportError:
        ffmpeg = _ffmpeg()
        if not ffmpeg:
            print("Need OpenCV or FFmpeg. Try:", file=sys.stderr)
            print("  pip install opencv-python-headless", file=sys.stderr)
            print("  brew install ffmpeg", file=sys.stderr)
            return 1
        generate_with_ffmpeg(ffmpeg)
    print()
    print("Use in Chakshu:")
    print(f"  Primary: {OUT / 'primary-left.mp4'}")
    print(f"  Inset:   {OUT / 'inset-right.mp4'}")
    print(f"  Demo side-by-side: {OUT / 'demo-side-by-side.mp4'}")
    print(f"  Demo PiP:          {OUT / 'demo-pip.mp4'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
