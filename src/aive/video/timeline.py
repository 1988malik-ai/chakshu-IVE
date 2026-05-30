"""
Forensic-grade video timeline — full index, cache, keyframe track.

Author: Mohit M
"""

from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any

from aive.analysis.frame_metadata import filter_frames, load_frame_index
from aive.analysis.stream import FrameInfo, StreamAnalyzer
from aive.video.timeline_cache import TimelineCache


def detect_vfr(frames: list[FrameInfo]) -> dict[str, Any]:
    if len(frames) < 3:
        return {"vfr": False, "avg_fps": None, "pts_deltas": []}
    deltas = [frames[i + 1].pts - frames[i].pts for i in range(len(frames) - 1) if frames[i + 1].pts > frames[i].pts]
    if not deltas:
        return {"vfr": False, "avg_fps": None, "pts_deltas": []}
    mean = statistics.mean(deltas)
    stdev = statistics.pstdev(deltas) if len(deltas) > 1 else 0.0
    vfr = stdev > max(0.002, mean * 0.08)
    avg_fps = 1.0 / mean if mean > 0 else None
    return {
        "vfr": vfr,
        "avg_fps": avg_fps,
        "mean_delta_sec": mean,
        "stdev_delta_sec": stdev,
        "sample_count": len(deltas),
    }


def _timecode(sec: float, fps: float = 30.0) -> str:
    if sec < 0:
        sec = 0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    f = int((sec % 1) * fps) if fps > 0 else 0
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def build_timeline(path: Path, limit: int = 25000, force_refresh: bool = False) -> dict[str, Any]:
    path = path.expanduser().resolve()
    cache = TimelineCache()
    if not force_refresh:
        cached = cache.get(path)
        if cached and cached.get("frame_sample_count", 0) > 0:
            cached["from_cache"] = True
            return cached

    analyzer = StreamAnalyzer()
    streams = analyzer.probe_streams(path)
    stream = streams[0] if streams else None
    frames = load_frame_index(path, limit=limit)

    # Ensure I-frames via dedicated pass when types are mostly unknown
    unknown_ratio = sum(1 for f in frames if f.frame_type == "?") / max(len(frames), 1)
    if unknown_ratio > 0.5 and analyzer.last_index_source.startswith("opencv"):
        from aive.codecs.ffmpeg_bin import get_ffmpeg_exe

        ff = get_ffmpeg_exe()
        if ff:
            from aive.analysis.stream import _extract_via_ffmpeg_showinfo

            iframe_data = _extract_via_ffmpeg_showinfo(path, ff, 5000, skip_non_key=True)
            if iframe_data:
                iframe_pts = {round(d["pts"], 4) for d in iframe_data}
                frames = [
                    FrameInfo(
                        index=f.index,
                        pts=f.pts,
                        dts=f.dts,
                        frame_type="I" if round(f.pts, 4) in iframe_pts or f.key_frame else f.frame_type,
                        key_frame=f.key_frame or round(f.pts, 4) in iframe_pts,
                        size=f.size,
                    )
                    for f in frames
                ]
                analyzer._last_index_source = "hybrid-opencv-ffmpeg-i"

    vfr = detect_vfr(frames)
    summary: dict[str, int] = {"I": 0, "P": 0, "B": 0, "?": 0}
    for f in frames:
        key = f.frame_type if f.frame_type in summary else "?"
        summary[key] += 1

    duration = frames[-1].pts if frames else 0.0
    if duration <= 0 and frames:
        duration = max(f.pts for f in frames)
    if duration <= 0 and stream and stream.duration:
        duration = stream.duration

    fps = stream.fps if stream else vfr.get("avg_fps")
    keyframes = [
        {"index": f.index, "pts": f.pts, "type": f.frame_type, "size": f.size}
        for f in frames
        if f.frame_type == "I" or f.key_frame
    ]

    sizes = [f.size for f in frames if f.size]
    result = {
        "path": str(path),
        "duration": duration,
        "fps": fps,
        "width": stream.width if stream else None,
        "height": stream.height if stream else None,
        "codec": stream.codec if stream else None,
        "frame_sample_count": len(frames),
        "iframe_count": len(keyframes),
        "summary": summary,
        "vfr": vfr,
        "index_source": analyzer.last_index_source,
        "index_quality": "forensic" if analyzer.last_index_source in (
            "ffprobe", "ffmpeg-showinfo-full", "ffmpeg-showinfo", "hybrid-opencv-ffmpeg-i"
        ) else "standard",
        "from_cache": False,
        "timecode_at_zero": _timecode(0, fps or 30),
        "avg_frame_bytes": sum(sizes) / len(sizes) if sizes else None,
        "keyframes": keyframes,
        "frames": [
            {
                "index": f.index,
                "pts": f.pts,
                "type": f.frame_type,
                "key_frame": f.key_frame,
                "size": f.size,
            }
            for f in frames
        ],
    }
    cache.put(path, result)
    return result


def frame_at_step(frames: list[FrameInfo], current_index: int, delta: int) -> FrameInfo | None:
    if not frames:
        return None
    indices = [f.index for f in frames]
    try:
        pos = indices.index(current_index)
    except ValueError:
        pos = min(range(len(indices)), key=lambda i: abs(indices[i] - current_index))
    pos = max(0, min(len(frames) - 1, pos + delta))
    return frames[pos]


def nearest_iframe(frames: list[FrameInfo], time_sec: float) -> FrameInfo | None:
    i_frames = [f for f in frames if f.frame_type == "I" or f.key_frame]
    if not i_frames:
        return None
    before = [f for f in i_frames if f.pts <= time_sec]
    return max(before, key=lambda f: f.pts) if before else min(i_frames, key=lambda f: f.pts)


def filter_timeline(
    path: Path,
    types: list[str] | None = None,
    key_frames_only: bool = False,
    start_sec: float | None = None,
    end_sec: float | None = None,
    limit: int = 25000,
) -> dict[str, Any]:
    frames = load_frame_index(path, limit=limit)
    filtered = filter_frames(
        frames,
        types=types,
        key_frames_only=key_frames_only,
        min_pts=start_sec,
        max_pts=end_sec,
    )
    return {
        "path": str(path),
        "match_count": len(filtered),
        "frames": [
            {"index": f.index, "pts": f.pts, "type": f.frame_type, "key_frame": f.key_frame}
            for f in filtered[:500]
        ],
    }
