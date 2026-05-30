"""Example workflows and learning resources (R-196)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from aive.brand import PRODUCT_NAME

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_DIR = _PROJECT_ROOT / "examples"
WORKFLOWS_DIR = EXAMPLES_DIR / "workflows"


def list_examples() -> list[dict[str, Any]]:
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    for path in sorted(WORKFLOWS_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
        items.append({
            "id": path.stem,
            "title": data.get("title", path.stem.replace("-", " ").title()),
            "description": data.get("description", ""),
            "phase": data.get("phase", ""),
            "steps": data.get("steps", []),
            "path": str(path),
        })
    readme = EXAMPLES_DIR / "README.md"
    if readme.exists():
        items.insert(0, {
            "id": "readme",
            "title": f"{PRODUCT_NAME} Quick Start",
            "description": "Overview and setup guide",
            "phase": "intro",
            "steps": ["Read examples/README.md"],
            "path": str(readme),
        })
    return items


def load_example(example_id: str) -> dict[str, Any]:
    if example_id == "readme":
        readme = EXAMPLES_DIR / "README.md"
        return {"id": "readme", "content": readme.read_text(encoding="utf-8") if readme.exists() else ""}
    path = WORKFLOWS_DIR / f"{example_id}.yaml"
    if not path.exists():
        return {"error": f"Example not found: {example_id}"}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {"id": example_id, "workflow": data, "path": str(path)}
