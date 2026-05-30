"""AI-IVE entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


def _load_config() -> dict:
    candidates = [
        Path(__file__).resolve().parents[2] / "config" / "app.yaml",
        Path.cwd() / "config" / "app.yaml",
    ]
    for p in candidates:
        if p.exists():
            with open(p) as f:
                return yaml.safe_load(f) or {}
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AI-IVE (legacy PyQt6 UI). For React UI use: python -m aive.api.server + npm run dev in frontend/"
    )
    parser.add_argument("--locale", default=None, help="UI locale code")
    parser.add_argument("--log", action="store_true", help="Enable operation logging")
    parser.add_argument("--high-contrast", action="store_true")
    args = parser.parse_args()

    config = _load_config()
    app_cfg = config.get("app", {})
    locale = args.locale or config.get("locale", "en")
    logging_cfg = config.get("logging", {})
    enable_log = args.log or logging_cfg.get("enabled", False)

    from aive.license.protection import check_license

    status = check_license(trial_days=config.get("license", {}).get("trial_days", 14) or 14)
    if not status.valid:
        print(f"License: {status.message}", file=sys.stderr)

    from aive.ui.main_window import run_app

    return run_app(locale=locale, enable_logging=enable_log)


if __name__ == "__main__":
    sys.exit(main())
