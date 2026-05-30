"""Video stream analysis — timestamps, demux, I/P/B frame types."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aive.codecs.ffmpeg_bin import get_ffmpeg_exe, get_ffprobe_exe
from aive.imaging import HAS_CV2

if HAS_CV2:
    import cv2

_DURATION_RE = re.compile(r"Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d+)")
_VIDEO_LINE_RE = re.compile(
    r"Video:.*?,\s*(\d+)x(\d+).*?(?:(\d+(?:\.\d+)?)\s*fps|(\d+(?:\.\d+)?)\s*tbr)",
    re.IGNORECASE,
)


@dataclass
class FrameInfo:
    index: int
    pts: float
    dts: float | None
    frame_type: str  # I, P, B, unknown
    key_frame: bool
    size: int | None = None


@dataclass
class StreamInfo:
    index: int
    codec: str
    width: int
    height: int
    fps: float | None
    duration: float | None
    time_base: str


def _parse_duration(text: str) -> float | None:
    m = _DURATION_RE.search(text)
    if not m:
        return None
    h, mn, s = m.groups()
    return int(h) * 3600 + int(mn) * 60 + float(s)


def _probe_via_ffmpeg_stderr(path: Path, ffmpeg: str) -> list[StreamInfo]:
    r = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(path)],
        capture_output=True,
        text=True,
    )
    stderr = r.stderr or ""
    duration = _parse_duration(stderr)
    vm = _VIDEO_LINE_RE.search(stderr)
    if not vm:
        return []
    w, h, fps1, fps2 = vm.groups()
    fps = float(fps1 or fps2 or 0) or None
    codec = "unknown"
    if "h264" in stderr.lower():
        codec = "h264"
    elif "hevc" in stderr.lower() or "h265" in stderr.lower():
        codec = "hevc"
    return [
        StreamInfo(
            index=0,
            codec=codec,
            width=int(w),
            height=int(h),
            fps=fps,
            duration=duration,
            time_base="1/90000",
        )
    ]


def _extract_via_ffmpeg_showinfo(path: Path, ffmpeg: str, limit: int, skip_non_key: bool = False) -> list[dict[str, Any]]:
    cmd = [ffmpeg, "-hide_banner"]
    if skip_non_key:
        cmd.append("-skip_frame")
        cmd.append("nokey")
    cmd.extend(["-i", str(path), "-vf", "showinfo"])
    if limit > 0:
        cmd.extend(["-frames:v", str(limit)])
    cmd.extend(["-f", "null", "-"])
    r = subprocess.run(cmd, capture_output=True, text=True)
    text = (r.stderr or "") + (r.stdout or "")
    frames: list[dict[str, Any]] = []
    seen: set[int] = set()
    for line in text.splitlines():
        if "n:" not in line:
            continue
        idx = pts = ftype = None
        is_key = False
        m = re.search(r"n:\s*(\d+).*?pts_time:([\d.]+)", line)
        if m:
            idx, pts = m.groups()
        tm = re.search(r"type:([IPB])", line, re.I)
        if tm:
            ftype = tm.group(1).upper()
        km = re.search(r"iskey:(\d)", line)
        if km:
            is_key = km.group(1) == "1"
        if ftype is None and is_key:
            ftype = "I"
        if idx is None or pts is None:
            continue
        ftype = ftype or "?"
        n = int(idx)
        if n in seen:
            continue
        seen.add(n)
        frames.append(
            {
                "pts": float(pts),
                "dts": None,
                "key_frame": bool(is_key),
                "type": ftype if ftype in ("I", "P", "B") else ("I" if is_key else "?"),
                "size": None,
            }
        )
        if len(frames) >= limit:
            break
    return frames


def _extract_via_opencv(path: Path, limit: int) -> list[dict[str, Any]]:
    if not HAS_CV2:
        return []
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    if fps <= 0:
        fps = 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    count = min(total if total > 0 else limit, limit)
    cap.release()
    if count <= 0:
        count = min(limit, 300)
    return [
        {
            "pts": i / fps,
            "dts": None,
            "key_frame": i == 0,
            "type": "?",
            "size": None,
        }
        for i in range(count)
    ]


class StreamAnalyzer:
    def __init__(self, ffprobe: str | None = None, ffmpeg: str | None = None) -> None:
        self.ffprobe = ffprobe or get_ffprobe_exe() or "ffprobe"
        self.ffmpeg = ffmpeg or get_ffmpeg_exe() or "ffmpeg"
        self._last_index_source: str = "none"

    @property
    def last_index_source(self) -> str:
        return self._last_index_source

    def probe_streams(self, path: Path) -> list[StreamInfo]:
        fp = get_ffprobe_exe()
        if fp:
            r = subprocess.run(
                [
                    fp,
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_streams",
                    str(path),
                ],
                capture_output=True,
                text=True,
            )
            if r.returncode == 0:
                data = json.loads(r.stdout)
                out = []
                for s in data.get("streams", []):
                    if s.get("codec_type") != "video":
                        continue
                    fps = None
                    if s.get("r_frame_rate"):
                        num, den = s["r_frame_rate"].split("/")
                        den_f = float(den) or 1.0
                        fps = float(num) / den_f
                    out.append(
                        StreamInfo(
                            index=s.get("index", 0),
                            codec=s.get("codec_name", "unknown"),
                            width=int(s.get("width", 0)),
                            height=int(s.get("height", 0)),
                            fps=fps,
                            duration=float(s.get("duration", 0) or 0) or None,
                            time_base=s.get("time_base", "1/90000"),
                        )
                    )
                if out:
                    return out

        ff = get_ffmpeg_exe()
        if ff:
            streams = _probe_via_ffmpeg_stderr(path, ff)
            if streams:
                return streams

        if HAS_CV2:
            cap = cv2.VideoCapture(str(path))
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS) or None
                fc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or None
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                dur = (fc / fps) if fc and fps and fps > 0 else None
                cap.release()
                return [
                    StreamInfo(
                        index=0,
                        codec="opencv",
                        width=w,
                        height=h,
                        fps=fps,
                        duration=dur,
                        time_base="1/fps",
                    )
                ]
        return []

    def extract_timestamps(self, path: Path, stream_index: int = 0, limit: int = 5000) -> list[dict[str, Any]]:
        fp = get_ffprobe_exe()
        if fp:
            r = subprocess.run(
                [
                    fp,
                    "-v",
                    "quiet",
                    "-select_streams",
                    f"v:{stream_index}",
                    "-show_frames",
                    "-show_entries",
                    "frame=pts_time,pkt_dts_time,key_frame,pict_type,pkt_size",
                    "-of",
                    "json",
                    str(path),
                ],
                capture_output=True,
                text=True,
            )
            if r.returncode == 0:
                frames = json.loads(r.stdout).get("frames", [])
                if frames:
                    self._last_index_source = "ffprobe"
                    return [
                        {
                            "pts": float(f.get("pts_time", 0)),
                            "dts": float(f["pkt_dts_time"]) if f.get("pkt_dts_time") else None,
                            "key_frame": f.get("key_frame") == 1,
                            "type": f.get("pict_type", "?"),
                            "size": int(f["pkt_size"]) if f.get("pkt_size") else None,
                        }
                        for f in frames[:limit]
                    ]

        ff = get_ffmpeg_exe()
        if ff:
            via_ff = _extract_via_ffmpeg_showinfo(path, ff, limit)
            if via_ff:
                self._last_index_source = "ffmpeg-showinfo"
                return via_ff
            # Full scan without frame cap (longer, stronger index)
            if limit >= 5000:
                via_full = _extract_via_ffmpeg_showinfo(path, ff, 0)
                if via_full:
                    self._last_index_source = "ffmpeg-showinfo-full"
                    return via_full[:limit] if limit > 0 else via_full

        via_cv = _extract_via_opencv(path, limit)
        if via_cv:
            self._last_index_source = "opencv-cfr"
            return via_cv

        self._last_index_source = "none"
        return []

    def demux_stream(
        self, path: Path, stream_index: int, output_path: Path, codec_copy: bool = True
    ) -> dict[str, Any]:
        if not get_ffmpeg_exe():
            return {"success": False, "error": "ffmpeg not found"}
        cmd = [
            self.ffmpeg,
            "-y",
            "-i",
            str(path),
            "-map",
            f"0:{stream_index}",
            "-c",
            "copy" if codec_copy else "libx264",
            str(output_path),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        return {"success": r.returncode == 0, "stderr": r.stderr}

    def analyze_frame_types(self, path: Path, limit: int = 5000) -> list[FrameInfo]:
        timestamps = self.extract_timestamps(path, limit=limit)[:limit]
        return [
            FrameInfo(
                index=i,
                pts=t["pts"],
                dts=t.get("dts"),
                frame_type=t.get("type", "?"),
                key_frame=t.get("key_frame", False),
                size=t.get("size"),
            )
            for i, t in enumerate(timestamps)
        ]

    def frame_type_summary(self, path: Path) -> dict[str, int]:
        frames = self.analyze_frame_types(path)
        summary: dict[str, int] = {"I": 0, "P": 0, "B": 0, "?": 0}
        for f in frames:
            key = f.frame_type if f.frame_type in summary else "?"
            summary[key] += 1
        return summary
