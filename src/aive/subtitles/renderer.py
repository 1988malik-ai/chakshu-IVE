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
        content = path.read_text(encoding="utf-8", errors="replace")
        cues = []
        sync_pattern = re.compile(
            r"<SYNC Start=(\d+)><P Class=\w+>(.*?)</SYNC>", re.DOTALL | re.IGNORECASE
        )
        matches = list(sync_pattern.finditer(content))
        for i, m in enumerate(matches):
            start_ms = int(m.group(1))
            text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            end_ms = int(matches[i + 1].group(1)) if i + 1 < len(matches) else start_ms + 3000
            cues.append(
                SubtitleCue(i + 1, start_ms / 1000.0, end_ms / 1000.0, text)
            )
        return cues

    @classmethod
    def load(cls, path: Path) -> list[SubtitleCue]:
        ext = path.suffix.lower()
        if ext == ".srt":
            return cls.parse_srt(path)
        if ext == ".smi":
            return cls.parse_smi(path)
        return cls.parse_srt(path)


def ffmpeg_subtitle_filter(path: Path) -> str:
    escaped = str(path).replace("\\", "/").replace(":", "\\:")
    return f"subtitles='{escaped}'"
