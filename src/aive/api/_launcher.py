"""PyInstaller / CLI entry — serves API + built React static files."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from aive.api.config import get_api_host, get_api_port


def _default_frontend_dist() -> str | None:
    env = os.environ.get("AIVE_FRONTEND_DIST")
    if env and Path(env).is_dir():
        return env
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled = Path(meipass) / "frontend-dist"
            if bundled.is_dir():
                return str(bundled)
        exe_dir = Path(sys.executable).resolve().parent
        for name in ("frontend-dist", "frontend", "dist"):
            candidate = exe_dir / name
            if candidate.is_dir() and (candidate / "index.html").is_file():
                return str(candidate)
            nested = exe_dir / name / "dist"
            if nested.is_dir() and (nested / "index.html").is_file():
                return str(nested)
    candidate = Path(__file__).resolve().parents[3] / "frontend" / "dist"
    if candidate.is_dir():
        return str(candidate)
    return None


def main_cli() -> None:
    parser = argparse.ArgumentParser(description="Chakshu API server")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--frontend-dist", default=None, help="Path to React build (frontend/dist)")
    args = parser.parse_args()

    dist = args.frontend_dist or _default_frontend_dist()

    from aive.api.server import run

    run(
        host=args.host or get_api_host(),
        port=args.port if args.port is not None else get_api_port(),
        frontend_dist=dist,
    )


if __name__ == "__main__":
    main_cli()
