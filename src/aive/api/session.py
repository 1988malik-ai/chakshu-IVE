"""In-memory session for current edit state (preview + undo)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from aive.filters.catalog import get_filter, FilterDomain
from aive.filters.engine import build_filter_chain
from aive.imaging import HAS_CV2, bgr_from_bytes, bgr_to_jpeg_base64
from aive.media.loader import MediaLibrary, MediaType
from aive.media.video_frame import extract_frame_bgr, is_video_filename
from aive.undo.stack import UndoStack

if HAS_CV2:
    import cv2


@dataclass
class MediaSession:
    id: str
    source_path: str | None = None
    media_type: str = "image"
    frame: np.ndarray | None = None
    master_frame: np.ndarray | None = None  # non-destructive original for forensics
    filter_chain: list[tuple[str, dict[str, Any] | None]] = field(default_factory=list)
    undo: UndoStack[np.ndarray] = field(default_factory=UndoStack)
    metadata: dict[str, Any] = field(default_factory=dict)
    evidence_id: str | None = None
    frame_index: int = 0
    time_sec: float = 0.0


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, MediaSession] = {}
        self._library = MediaLibrary()

    def create(self) -> MediaSession:
        sid = str(uuid.uuid4())
        session = MediaSession(id=sid)
        self._sessions[sid] = session
        return session

    def get(self, session_id: str) -> MediaSession | None:
        return self._sessions.get(session_id)

    def load_upload(self, session_id: str, data: bytes, filename: str, storage_path: str | None = None) -> MediaSession:
        if not data:
            raise ValueError("Empty file upload")

        if storage_path:
            path = Path(storage_path).expanduser()
            if path.exists() and is_video_filename(filename):
                return self.load_path(session_id, str(path))
            if path.exists():
                return self.load_path(session_id, str(path))

        if is_video_filename(filename):
            raise ValueError(
                "Video must be saved to disk before loading. "
                "Use evidence ingest (upload) or /api/media/load-path with a full file path."
            )

        if session_id not in self._sessions:
            self._sessions[session_id] = MediaSession(id=session_id)
        session = self._sessions[session_id]

        frame = bgr_from_bytes(data, filename)
        session.source_path = storage_path or filename
        session.media_type = "image"
        session.filter_chain.clear()
        session.undo = UndoStack()
        session.master_frame = frame.copy()
        session.frame = frame.copy()
        session.undo.push(session.frame, "load")
        return session

    def load_path(self, session_id: str, path: str) -> MediaSession:
        p = Path(path)
        if session_id not in self._sessions:
            self._sessions[session_id] = MediaSession(id=session_id)
        session = self._sessions[session_id]

        mt = self._library.classify(p)
        session.source_path = str(p)
        session.media_type = mt.value

        if mt in (MediaType.IMAGE, MediaType.RAW):
            frame = self._library.load_image(p)
            if frame is None:
                data = p.read_bytes()
                frame = bgr_from_bytes(data, p.name)
            session.filter_chain.clear()
            session.undo = UndoStack()
            session.master_frame = frame.copy()
            session.frame = frame.copy()
            session.undo.push(session.frame, "load")
        elif mt == MediaType.VIDEO:
            item = None
            try:
                item = self._library.open_video(p)
                session.metadata = dict(item.metadata) if item and item.metadata else {}
            except RuntimeError as e:
                if "OpenCV" in str(e):
                    session.metadata = {}
                else:
                    raise

            frame = None
            if item and item.capture:
                ok, frame = item.capture.read()
                item.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            if frame is None:
                frame = extract_frame_bgr(p, 0.0)
            if frame is None:
                raise ValueError(
                    "Could not read video frame. Install: pip install -r requirements-video.txt "
                    "and/or: pip install opencv-python-headless"
                )
            session.filter_chain.clear()
            session.undo = UndoStack()
            session.master_frame = frame.copy()
            session.frame = frame.copy()
            session.undo.push(session.frame, "load")
            if not session.metadata:
                from aive.video.seek import get_video_info

                try:
                    info = get_video_info(p)
                    session.metadata = {
                        "fps": info.get("fps"),
                        "duration": info.get("duration"),
                        "frame_count": info.get("frame_count"),
                    }
                except Exception:
                    pass
        else:
            raise ValueError(f"Unsupported media: {path}")
        return session

    def _render_from_master(self, session: MediaSession) -> np.ndarray:
        base = session.master_frame
        if base is None:
            raise ValueError("No master frame")
        if not session.filter_chain:
            return base.copy()
        return build_filter_chain(session.filter_chain).apply(base.copy())

    def _filter_allowed(self, filter_id: str, media_type: str) -> bool:
        spec = get_filter(filter_id)
        if spec is None:
            return False
        if spec.domain == FilterDomain.BOTH:
            return True
        if media_type == "video":
            return spec.domain == FilterDomain.VIDEO
        return spec.domain == FilterDomain.IMAGE

    @staticmethod
    def filter_domain_mismatch_message(filter_id: str, media_type: str) -> str:
        spec = get_filter(filter_id)
        if spec is None:
            return f"Unknown filter '{filter_id}'"
        return (
            f"Filter '{filter_id}' is for {spec.domain.value} evidence; "
            f"current session is {media_type}. Load matching evidence first."
        )

    def ensure_filter_allowed(self, filter_id: str, media_type: str) -> None:
        if not self._filter_allowed(filter_id, media_type):
            raise ValueError(self.filter_domain_mismatch_message(filter_id, media_type))

    def apply_filter(
        self,
        session_id: str,
        filter_id: str,
        params: dict | None = None,
        *,
        insert_at: int | None = None,
    ) -> MediaSession:
        session = self._require(session_id)
        if session.master_frame is None:
            raise ValueError("No frame loaded — upload an image or load a video frame first")
        self.ensure_filter_allowed(filter_id, session.media_type)
        session.undo.push(session.frame, "before_filter")
        entry = (filter_id, params)
        if insert_at is not None and 0 <= insert_at <= len(session.filter_chain):
            session.filter_chain.insert(insert_at, entry)
            pop_index = insert_at
        else:
            session.filter_chain.append(entry)
            pop_index = len(session.filter_chain) - 1
        try:
            session.frame = self._render_from_master(session)
        except Exception:
            session.filter_chain.pop(pop_index)
            session.undo.undo()
            raise
        return session

    def seek_video(self, session_id: str, time_sec: float) -> MediaSession:
        session = self._require(session_id)
        if session.media_type != "video":
            raise ValueError("Session is not video")
        path = Path(session.source_path or "").expanduser()
        if not path.is_file():
            raise ValueError(f"Video file not found: {session.source_path}")
        frame = extract_frame_bgr(path, time_sec)
        if frame is None:
            raise ValueError("Could not extract frame at this time")
        session.time_sec = time_sec
        fps = session.metadata.get("fps")
        if fps and fps > 0 and time_sec >= 0:
            session.frame_index = int(round(time_sec * fps))
        session.master_frame = frame.copy()
        session.frame = self._render_from_master(session)
        session.undo.push(session.frame, f"seek_{time_sec:.2f}")
        return session

    def reset_enhancement(self, session_id: str) -> MediaSession:
        session = self._require(session_id)
        session.filter_chain.clear()
        if session.master_frame is not None:
            session.frame = session.master_frame.copy()
        return session

    def remove_filter_at(self, session_id: str, index: int) -> MediaSession:
        """Remove one filter from the chain and re-render from master (non-destructive)."""
        session = self._require(session_id)
        if session.master_frame is None:
            raise ValueError("No frame loaded")
        if index < 0 or index >= len(session.filter_chain):
            raise IndexError(f"Filter index out of range: {index}")
        session.undo.push(session.frame, "before_remove_filter")
        session.filter_chain.pop(index)
        session.frame = self._render_from_master(session)
        return session

    def set_filter_chain(self, session_id: str, chain: list[tuple[str, dict | None]]) -> MediaSession:
        session = self._require(session_id)
        for filter_id, _ in chain:
            self.ensure_filter_allowed(filter_id, session.media_type)
        session.filter_chain = list(chain)
        session.frame = self._render_from_master(session)
        return session

    def undo(self, session_id: str) -> MediaSession:
        session = self._require(session_id)
        state = session.undo.undo()
        if state is not None:
            session.frame = state
            if session.filter_chain:
                session.filter_chain.pop()
        return session

    def redo(self, session_id: str) -> MediaSession:
        session = self._require(session_id)
        state = session.undo.redo()
        if state is not None:
            session.frame = state
        return session

    def _require(self, session_id: str) -> MediaSession:
        s = self._sessions.get(session_id)
        if s is None:
            raise KeyError(f"Unknown session: {session_id}")
        return s

    @staticmethod
    def frame_to_base64_jpeg(frame: np.ndarray, quality: int = 92) -> str:
        return bgr_to_jpeg_base64(frame, quality)


sessions = SessionManager()
