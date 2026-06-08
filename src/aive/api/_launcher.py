"""PyInstaller / CLI entry — serves API + built React static files."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from aive.api.config import get_api_host, get_api_port


def _valid_dist(path: str | Path | None) -> str | None:
    if not path:
        return None
    p = Path(path)
    if p.is_dir() and (p / "index.html").is_file():
        return str(p.resolve())
    return None


def resolve_frontend_dist(cli_path: str | None = None) -> str | None:
    """Pick first UI folder that contains index.html (bundled exe path preferred when frozen)."""
    candidates: list[Path] = []

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "frontend-dist")
        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend(
            exe_dir / name
            for name in ("frontend-dist", "frontend", "dist")
        )

    if cli_path:
        candidates.append(Path(cli_path))

    env = os.environ.get("AIVE_FRONTEND_DIST")
    if env:
        candidates.append(Path(env))

    candidates.append(Path(__file__).resolve().parents[3] / "frontend" / "dist")

    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        valid = _valid_dist(candidate)
        if valid:
            return valid
    return None


def main_cli() -> None:
    parser = argparse.ArgumentParser(description="Chakshu API server")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--frontend-dist", default=None, help="Path to React build (frontend/dist)")
    args = parser.parse_args()

    dist = resolve_frontend_dist(args.frontend_dist)

    from aive.api.server import run

    run(
        host=args.host or get_api_host(),
        port=args.port if args.port is not None else get_api_port(),
        frontend_dist=dist,
    )


if __name__ == "__main__":
    main_cli()
