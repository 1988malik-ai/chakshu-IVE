"""
Per-frame metadata filtering and region analysis.

Author: Mohit M
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from aive.analysis.stream import FrameInfo, StreamAnalyzer


def load_frame_index(path: Path, limit: int = 5000) -> list[FrameInfo]:
    return StreamAnalyzer().analyze_frame_types(path, limit=limit)


def filter_frames(
    frames: list[FrameInfo],
    types: list[str] | None = None,
    key_frames_only: bool = False,
    min_pts: float | None = None,
    max_pts: float | None = None,
    min_size: int | None = None,
) -> list[FrameInfo]:
    out = frames
    if types:
        allowed = {t.upper() for t in types}
        out = [f for f in out if f.frame_type.upper() in allowed]
    if key_frames_only:
        out = [f for f in out if f.key_frame]
    if min_pts is not None:
        out = [f for f in out if f.pts >= min_pts]
    if max_pts is not None:
        out = [f for f in out if f.pts <= max_pts]
    if min_size is not None:
        out = [f for f in out if f.size is not None and f.size >= min_size]
    return out


def region_summary(frames: list[FrameInfo], start_sec: float, end_sec: float) -> dict[str, Any]:
    region = [f for f in frames if start_sec <= f.pts <= end_sec]
    counts: dict[str, int] = {"I": 0, "P": 0, "B": 0, "?": 0}
    sizes: list[int] = []
    for f in region:
        key = f.frame_type if f.frame_type in counts else "?"
        counts[key] += 1
        if f.size:
            sizes.append(f.size)
    return {
        "start_sec": start_sec,
        "end_sec": end_sec,
        "frame_count": len(region),
        "types": counts,
        "avg_pkt_size": sum(sizes) / len(sizes) if sizes else None,
        "frames": [{"index": f.index, "pts": f.pts, "type": f.frame_type} for f in region[:200]],
    }


def analyze_file(path: Path, limit: int = 5000) -> dict[str, Any]:
    frames = load_frame_index(path, limit)
    summary: dict[str, int] = {"I": 0, "P": 0, "B": 0, "?": 0}
    for f in frames:
        key = f.frame_type if f.frame_type in summary else "?"
        summary[key] += 1
    return {
        "path": str(path),
        "frame_count": len(frames),
        "summary": summary,
        "frames": [
            {
                "index": f.index,
                "pts": f.pts,
                "dts": f.dts,
                "type": f.frame_type,
                "key_frame": f.key_frame,
                "size": f.size,
            }
            for f in frames
        ],
    }
