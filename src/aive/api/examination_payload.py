"""Shared examination API fields — original vs enhanced previews."""

from __future__ import annotations

from typing import Any

from aive.api.session import MediaSession, sessions


def examination_preview_fields(session: MediaSession) -> dict[str, Any]:
    """JPEG previews for current frame and non-destructive master (original)."""
    fields: dict[str, Any] = {
        "filter_chain": [f[0] for f in session.filter_chain],
        "is_enhanced": len(session.filter_chain) > 0,
        "time_sec": session.time_sec,
        "frame_index": session.frame_index,
        "media_type": session.media_type,
        "source_path": session.source_path,
    }
    if session.frame is not None:
        fields["preview"] = sessions.frame_to_base64_jpeg(session.frame)
    if session.master_frame is not None:
        fields["preview_original"] = sessions.frame_to_base64_jpeg(session.master_frame)
    return fields
