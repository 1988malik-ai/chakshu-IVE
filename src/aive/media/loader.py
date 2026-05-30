"""Media loading — images, RAW, multi-video, folder tree."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from aive.imaging import HAS_CV2, bgr_from_bytes

if HAS_CV2:
    import cv2

from aive.codecs.decoders import get_decoder


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp", ".gif"}
RAW_EXTENSIONS = {".cr2", ".nef", ".arw", ".dng", ".orf", ".rw2", ".raf", ".pef"}
VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".mxf", ".ts", ".m4v", ".mpg", ".mpeg"
}


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    RAW = "raw"
    UNKNOWN = "unknown"


@dataclass
class MediaItem:
    path: Path
    media_type: MediaType
    name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    capture: Any = None

    def __post_init__(self) -> None:
        if not self.name:
            self.name = self.path.name


@dataclass
class FolderNode:
    path: Path
    children: list[FolderNode] = field(default_factory=list)
    files: list[Path] = field(default_factory=list)


class MediaLibrary:
    def __init__(self, max_videos: int = 8) -> None:
        self.max_videos = max_videos
        self.items: list[MediaItem] = []
        self.root_folders: list[FolderNode] = []
        self._decoder = get_decoder("ffmpeg")

    @staticmethod
    def classify(path: Path) -> MediaType:
        ext = path.suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            return MediaType.IMAGE
        if ext in RAW_EXTENSIONS:
            return MediaType.RAW
        if ext in VIDEO_EXTENSIONS:
            return MediaType.VIDEO
        return MediaType.UNKNOWN

    def scan_folder(self, folder: Path, recursive: bool = True) -> FolderNode:
        node = FolderNode(path=folder)
        try:
            for entry in sorted(folder.iterdir()):
                if entry.is_dir() and recursive:
                    node.children.append(self.scan_folder(entry, recursive))
                elif entry.is_file() and self.classify(entry) != MediaType.UNKNOWN:
                    node.files.append(entry)
        except PermissionError:
            pass
        self.root_folders.append(node)
        return node

    def load_image(self, path: Path) -> np.ndarray | None:
        mt = self.classify(path)
        if mt == MediaType.RAW:
            try:
                import rawpy  # type: ignore

                with rawpy.imread(str(path)) as raw:
                    rgb = raw.postprocess()
                if HAS_CV2:
                    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                return rgb[:, :, ::-1].copy()
            except ImportError:
                return None

        if HAS_CV2:
            img = cv2.imread(str(path))
            if img is not None:
                return img

        try:
            return bgr_from_bytes(path.read_bytes(), path.name)
        except Exception:
            return None

    def open_video(self, path: Path) -> MediaItem | None:
        if not HAS_CV2:
            raise RuntimeError("Video requires OpenCV")

        video_count = sum(1 for i in self.items if i.media_type == MediaType.VIDEO)
        if video_count >= self.max_videos:
            raise RuntimeError(f"Maximum {self.max_videos} simultaneous videos")

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            probe = self._decoder.probe(path)
            item = MediaItem(path=path, media_type=MediaType.VIDEO, metadata=probe)
            self.items.append(item)
            return item

        meta = {
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        }
        item = MediaItem(path=path, media_type=MediaType.VIDEO, metadata=meta, capture=cap)
        self.items.append(item)
        return item

    def add_file(self, path: Path) -> MediaItem | None:
        mt = self.classify(path)
        if mt == MediaType.VIDEO:
            return self.open_video(path)
        if mt in (MediaType.IMAGE, MediaType.RAW):
            item = MediaItem(path=path, media_type=mt)
            self.items.append(item)
            return item
        return None

    def close_all(self) -> None:
        for item in self.items:
            if item.capture is not None:
                item.capture.release()
        self.items.clear()
