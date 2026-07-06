"""Single-file application logging for Chakshu / AI-IVE."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG = logging.getLogger("aive")
_CONFIGURED = False


def log_file_path() -> Path:
    env = os.environ.get("AIVE_LOG_FILE", "").strip()
    if env:
        return Path(env).expanduser()
    return Path.home() / ".ai-ive" / "chakshu.log"


def configure_logging(level: int | None = None) -> Path:
    """Send all app, API, and uvicorn logs to one rotating file (+ console)."""
    global _CONFIGURED
    path = log_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    if level is None:
        level = logging.DEBUG if os.environ.get("AIVE_DEBUG") else logging.INFO

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        path,
        maxBytes=8_000_000,
        backupCount=1,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)

    root = logging.getLogger()
    if not _CONFIGURED:
        root.handlers.clear()
    root.setLevel(level)
    if not any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        root.addHandler(file_handler)
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in root.handlers):
        root.addHandler(console)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        child = logging.getLogger(name)
        child.handlers.clear()
        child.propagate = True

    if not _CONFIGURED:
        LOG.info("Chakshu logging → %s", path)
    _CONFIGURED = True
    return path
