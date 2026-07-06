"""Diagnostics — unified client/server log access."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from aive.log_config import log_file_path

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])
_LOG = logging.getLogger("aive.client")


class ClientLogBody(BaseModel):
    level: str = "error"
    context: str = ""
    message: str
    detail: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)


@router.post("/log")
def client_log(body: ClientLogBody) -> dict[str, Any]:
    """Append a UI-side error or warning to the shared log file."""
    parts = [p for p in (body.context, body.message) if p]
    msg = ": ".join(parts) if parts else body.message
    if body.detail:
        msg = f"{msg} | {body.detail}"
    if body.extra:
        msg = f"{msg} | {body.extra}"

    if body.level == "warn":
        _LOG.warning(msg)
    elif body.level == "info":
        _LOG.info(msg)
    else:
        _LOG.error(msg)

    path = log_file_path()
    return {"ok": True, "log_file": str(path)}


@router.get("/log-tail")
def log_tail(lines: int = 100) -> dict[str, Any]:
    """Return the last N lines from the shared log (for support / debugging)."""
    path = log_file_path()
    if not path.is_file():
        return {"path": str(path), "exists": False, "lines": []}
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    limit = max(1, min(lines, 500))
    return {"path": str(path), "exists": True, "lines": text[-limit:]}
