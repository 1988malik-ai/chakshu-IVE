"""PyInstaller / CLI entry — serves API + built React static files."""

from __future__ import annotations

import argparse
from pathlib import Path

from aive.api.config import get_api_host, get_api_port


def main_cli() -> None:
    parser = argparse.ArgumentParser(description="AI-IVE API server")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--frontend-dist", default=None, help="Path to React build (frontend/dist)")
    args = parser.parse_args()

    dist = args.frontend_dist
    if not dist:
        candidate = Path(__file__).resolve().parents[3] / "frontend" / "dist"
        if candidate.is_dir():
            dist = str(candidate)

    from aive.api.server import run

    run(
        host=args.host or get_api_host(),
        port=args.port if args.port is not None else get_api_port(),
        frontend_dist=dist,
    )


if __name__ == "__main__":
    main_cli()
