"""Subtitle rendering — SRT, SMI."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SubtitleCue:
    index: int
    start_sec: float
    end_sec: float
    text: str


class SubtitleParser:
    @staticmethod
    def parse_srt(path: Path) -> list[SubtitleCue]:
        try:
            import pysrt

            subs = pysrt.open(str(path))
            cues = []
            for i, sub in enumerate(subs):
                start = sub.start.ordinal / 1000.0
                end = sub.end.ordinal / 1000.0
                cues.append(SubtitleCue(i + 1, start, end, sub.text.replace("\n", " ")))
            return cues
        except Exception:
            return SubtitleParser._parse_srt_manual(path)

    @staticmethod
    def _parse_srt_manual(path: Path) -> list[SubtitleCue]:
        content = path.read_text(encoding="utf-8", errors="replace")
        blocks = re.split(r"\n\s*\n", content.strip())
        cues = []
        for block in blocks:
            lines = block.strip().splitlines()
            if len(lines) < 3:
                continue
            try:
                idx = int(lines[0])
            except ValueError:
                idx = len(cues) + 1
            times = lines[1]
            m = re.match(
                r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})",
                times,
            )
            if not m:
                continue
            g = [int(x) for x in m.groups()]

            def to_sec(h, mi, s, ms):
                return h * 3600 + mi * 60 + s + ms / 1000.0

            start = to_sec(g[0], g[1], g[2], g[3])
            end = to_sec(g[4], g[5], g[6], g[7])
            text = " ".join(lines[2:])
            cues.append(SubtitleCue(idx, start, end, text))
        return cues

    @staticmethod
    def parse_smi(path: Path) -> list[SubtitleCue]:
        raw = path.read_bytes()
        content = None
        for enc in ("utf-8", "utf-8-sig", "cp949", "latin-1"):
            try:
                content = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if content is None:
            content = raw.decode("utf-8", errors="replace")

        cues: list[SubtitleCue] = []
        sync_pattern = re.compile(
            r"<SYNC\s+Start=(\d+)[^>]*>(.*?)(?=<SYNC|$)",
            re.DOTALL | re.IGNORECASE,
        )
        matches = list(sync_pattern.finditer(content))
        for i, m in enumerate(matches):
            start_ms = int(m.group(1))
            block = m.group(2)
            p_match = re.search(r"<P[^>]*>(.*?)</P>", block, re.DOTALL | re.IGNORECASE)
            text_src = p_match.group(1) if p_match else block
            text = re.sub(r"<br\s*/?>", "\n", text_src, flags=re.IGNORECASE)
            text = re.sub(r"<[^>]+>", "", text).strip()
            if not text:
                continue
            end_ms = int(matches[i + 1].group(1)) if i + 1 < len(matches) else start_ms + 3000
            cues.append(
                SubtitleCue(len(cues) + 1, start_ms / 1000.0, end_ms / 1000.0, text)
            )
        return cues

    @classmethod
    def load(cls, path: Path) -> list[SubtitleCue]:
        ext = path.suffix.lower()
        if ext == ".srt":
            return cls.parse_srt(path)
        if ext == ".smi":
            return cls.parse_smi(path)
        if ext in {".ass", ".ssa"}:
            return cls.parse_srt(path)
        return cls.parse_srt(path)

    @classmethod
    def detect_format(cls, path: Path) -> str:
        ext = path.suffix.lower()
        if ext in {".srt", ".smi", ".ass", ".ssa"}:
            return ext.lstrip(".")
        return "srt"


def cue_at_time(cues: list[SubtitleCue], time_sec: float) -> SubtitleCue | None:
    t = float(time_sec)
    for cue in cues:
        if cue.start_sec <= t <= cue.end_sec:
            return cue
    return None


def cues_to_dicts(cues: list[SubtitleCue], limit: int = 2000) -> list[dict[str, Any]]:
    return [
        {
            "index": c.index,
            "start": c.start_sec,
            "end": c.end_sec,
            "text": c.text,
        }
        for c in cues[:limit]
    ]


def write_srt(cues: list[SubtitleCue], output_path: Path) -> Path:
    """Write cues as SRT (used when burning SMI via FFmpeg)."""

    def _tc(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        ms = int(round((sec % 1) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines: list[str] = []
    for i, c in enumerate(cues, start=1):
        lines.append(str(i))
        lines.append(f"{_tc(c.start_sec)} --> {_tc(c.end_sec)}")
        lines.append(c.text.replace("\n", "\n"))
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def ensure_ffmpeg_subtitle_path(subtitle_path: Path) -> Path:
    """FFmpeg subtitles filter is most reliable with SRT."""
    if subtitle_path.suffix.lower() != ".smi":
        return subtitle_path
    cues = SubtitleParser.parse_smi(subtitle_path)
    if not cues:
        return subtitle_path
    out = subtitle_path.with_suffix(".chakshu-export.srt")
    return write_srt(cues, out)


def ffmpeg_subtitle_filter(path: Path) -> str:
    escaped = str(path).replace("\\", "/").replace(":", "\\:")
    return f"subtitles='{escaped}'"


def ffmpeg_subtitle_filter_styled(path: Path, style: dict[str, Any] | None = None) -> str:
    """R-121 — burn-in with ASS force_style customization."""
    escaped = str(path).replace("\\", "/").replace(":", "\\:")
    if not style:
        return f"subtitles='{escaped}'"
    parts = []
    mapping = {
        "font_name": "FontName",
        "font_size": "FontSize",
        "primary_colour": "PrimaryColour",
        "outline_colour": "OutlineColour",
        "back_colour": "BackColour",
        "bold": "Bold",
        "italic": "Italic",
        "border_style": "BorderStyle",
        "outline": "Outline",
        "shadow": "Shadow",
        "margin_v": "MarginV",
        "alignment": "Alignment",
    }
    for key, ass_key in mapping.items():
        if key in style and style[key] is not None:
            parts.append(f"{ass_key}={style[key]}")
    force = ",".join(parts) if parts else "FontSize=22,PrimaryColour=&H00FFFFFF,Outline=2"
    return f"subtitles='{escaped}':force_style='{force}'"


def burn_subtitles(
    video_path: Path,
    subtitle_path: Path,
    output_path: Path,
    style: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Burn styled subtitles into video via FFmpeg."""
    import subprocess

    from aive.codecs.ffmpeg_bin import require_ffmpeg

    try:
        ffmpeg = require_ffmpeg()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    sub_for_ff = ensure_ffmpeg_subtitle_path(subtitle_path)
    vf = ffmpeg_subtitle_filter_styled(sub_for_ff, style)
    cmd = [
        ffmpeg, "-y", "-i", str(video_path),
        "-vf", vf,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(output_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": r.returncode == 0,
        "command": " ".join(cmd),
        "output": str(output_path),
        "style": style or {},
        "stderr": r.stderr[-800:] if r.stderr else "",
    }
