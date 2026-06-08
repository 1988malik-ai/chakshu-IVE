"""Server ports — config/app.yaml, env vars, or defaults."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 9450
DEFAULT_FRONTEND_PORT = 9451


def _load_yaml() -> dict:
    bases: list[Path] = [Path.cwd()]
    try:
        import sys

        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            bases.insert(0, Path(sys._MEIPASS))
    except ImportError:
        pass
    bases.append(Path(__file__).resolve().parents[3])
    for base in bases:
        path = base / "config" / "app.yaml"
        if path.exists():
            with open(path) as f:
                return yaml.safe_load(f) or {}
    return {}


def get_api_host() -> str:
    return os.environ.get("AIVE_API_HOST") or _load_yaml().get("server", {}).get("api_host") or DEFAULT_API_HOST


def get_api_port() -> int:
    raw = os.environ.get("AIVE_API_PORT") or _load_yaml().get("server", {}).get("api_port")
    return int(raw) if raw is not None else DEFAULT_API_PORT


def get_frontend_port() -> int:
    raw = os.environ.get("AIVE_FRONTEND_PORT") or _load_yaml().get("server", {}).get("frontend_port")
    return int(raw) if raw is not None else DEFAULT_FRONTEND_PORT


def cors_origins() -> list[str]:
    port = get_frontend_port()
    origins = {
        f"http://localhost:{port}",
        f"http://127.0.0.1:{port}",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }
    extra = os.environ.get("AIVE_CORS_ORIGINS", "")
    for o in extra.split(","):
        o = o.strip()
        if o:
            origins.add(o)
    return sorted(origins)
