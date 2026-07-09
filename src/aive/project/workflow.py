"""Human-readable project format (YAML) + import from compatible tools."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_EXT = ".aive.yaml"
COMPATIBLE_EXTENSIONS = {".aive.yaml", ".aive.yml", ".json"}


@dataclass
class WorkflowStep:
    action: str
    timestamp: str
    settings: dict[str, Any] = field(default_factory=dict)
    references: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class AiveProject:
    """Human-readable workflow documentation format."""
    format_version: str = "1.0"
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Untitled Project"
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    media: list[dict[str, Any]] = field(default_factory=list)
    filter_pipeline: list[dict[str, Any]] = field(default_factory=list)
    bookmarks: list[dict[str, Any]] = field(default_factory=list)
    workflow_steps: list[WorkflowStep] = field(default_factory=list)
    export_settings: dict[str, Any] = field(default_factory=dict)
    report_template: str = "standard"
    metadata: dict[str, Any] = field(default_factory=dict)
    examination_notes: list[dict[str, Any]] = field(default_factory=list)

    def add_step(self, action: str, settings: dict | None = None, references: list | None = None) -> None:
        self.workflow_steps.append(
            WorkflowStep(
                action=action,
                timestamp=datetime.utcnow().isoformat(),
                settings=settings or {},
                references=references or [],
            )
        )
        self.updated = datetime.utcnow().isoformat()

    def to_yaml(self) -> str:
        data = {
            "aive_project": {
                "format_version": self.format_version,
                "project_id": self.project_id,
                "name": self.name,
                "created": self.created,
                "updated": self.updated,
                "media": self.media,
                "filter_pipeline": self.filter_pipeline,
                "bookmarks": self.bookmarks,
                "workflow_steps": [asdict(s) for s in self.workflow_steps],
                "export_settings": self.export_settings,
                "report_template": self.report_template,
                "metadata": self.metadata,
                "examination_notes": self.examination_notes,
            }
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)

    @classmethod
    def from_yaml(cls, text: str) -> AiveProject:
        data = yaml.safe_load(text)
        root = data.get("aive_project", data)
        steps = [WorkflowStep(**s) for s in root.get("workflow_steps", [])]
        return cls(
            format_version=root.get("format_version", "1.0"),
            project_id=root.get("project_id", str(uuid.uuid4())),
            name=root.get("name", "Imported"),
            created=root.get("created", datetime.utcnow().isoformat()),
            updated=root.get("updated", datetime.utcnow().isoformat()),
            media=root.get("media", []),
            filter_pipeline=root.get("filter_pipeline", []),
            bookmarks=root.get("bookmarks", []),
            workflow_steps=steps,
            export_settings=root.get("export_settings", {}),
            report_template=root.get("report_template", "standard"),
            metadata=root.get("metadata", {}),
            examination_notes=root.get("examination_notes", []),
        )

    def save(self, path: Path) -> Path:
        path = path if path.suffix else path.with_suffix(PROJECT_EXT)
        path.write_text(self.to_yaml(), encoding="utf-8")
        return path


class ProjectStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path.home() / ".ai-ive" / "projects"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._current: AiveProject | None = None

    @property
    def current(self) -> AiveProject:
        if self._current is None:
            self._current = AiveProject()
        return self._current

    def new_project(self, name: str) -> AiveProject:
        self._current = AiveProject(name=name)
        return self._current

    def load(self, path: Path) -> AiveProject:
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            self._current = _import_json_compatible(text)
        else:
            self._current = AiveProject.from_yaml(text)
        from aive.project import examination_notes as en

        en.hydrate_from_sidecar()
        return self._current

    def save_current(self, path: Path | None = None) -> Path:
        p = path or self.base_dir / f"{self.current.project_id}{PROJECT_EXT}"
        return self.current.save(p)

    def import_compatible(self, path: Path) -> AiveProject:
        """Import from AI-IVE YAML/JSON or simplified compatible JSON."""
        if path.suffix.lower() == ".json":
            self._current = _import_json_compatible(path.read_text(encoding="utf-8"))
            return self._current
        return self.load(path)


def inspect_compatible_project(path: Path) -> dict[str, Any]:
    """Return a strict, user-facing compatibility summary before import."""
    path = path.expanduser()
    ext = path.suffix.lower()
    summary: dict[str, Any] = {
        "path": str(path),
        "file_name": path.name,
        "extension": ext,
        "supported": ext in COMPATIBLE_EXTENSIONS,
        "format": "unknown",
        "warnings": [],
        "counts": {"media": 0, "filters": 0, "steps": 0, "bookmarks": 0, "notes": 0},
    }
    if ext not in COMPATIBLE_EXTENSIONS:
        summary["warnings"].append("Unsupported extension. Use .aive.yaml, .aive.yml, or compatible .json.")
        return summary

    try:
        text = path.read_text(encoding="utf-8")
        if ext == ".json":
            raw = json.loads(text)
            root = raw.get("aive_project", raw)
            summary["format"] = "aive_json" if "aive_project" in raw else "compatible_json"
        else:
            raw = yaml.safe_load(text) or {}
            root = raw.get("aive_project", raw)
            summary["format"] = "aive_yaml" if "aive_project" in raw else "yaml"
        if not isinstance(root, dict):
            summary["supported"] = False
            summary["warnings"].append("Project root is not an object.")
            return summary

        summary["project_id"] = root.get("project_id", "")
        summary["name"] = root.get("name") or root.get("project_name") or "Imported"
        summary["counts"] = {
            "media": len(root.get("media", root.get("assets", [])) or []),
            "filters": len(root.get("filter_pipeline", root.get("filters", [])) or []),
            "steps": len(root.get("workflow_steps", root.get("steps", root.get("workflow", []))) or []),
            "bookmarks": len(root.get("bookmarks", []) or []),
            "notes": len(root.get("examination_notes", root.get("notes", [])) or []),
        }
        if summary["counts"]["media"] == 0:
            summary["warnings"].append("No media entries found; evidence may need to be reloaded after import.")
        if summary["format"] in {"compatible_json", "yaml"}:
            summary["warnings"].append("Compatible import will normalize fields into Chakshu project format.")
    except Exception as exc:
        summary["supported"] = False
        summary["warnings"].append(f"Could not inspect project: {exc}")
    return summary


def _import_json_compatible(text: str) -> AiveProject:
    raw = json.loads(text)
    if "aive_project" in raw:
        return AiveProject.from_yaml(yaml.dump(raw))
    # Generic compatible: { "name", "steps", "media" }
    proj = AiveProject(name=raw.get("name", raw.get("project_name", "Imported")))
    for step in raw.get("steps", raw.get("workflow", [])):
        proj.add_step(
            step.get("action", step.get("type", "import")),
            settings=step.get("settings", step.get("params", {})),
            references=step.get("references", []),
        )
    proj.media = raw.get("media", raw.get("assets", []))
    proj.filter_pipeline = raw.get("filter_pipeline", raw.get("filters", []))
    proj.examination_notes = raw.get("examination_notes", raw.get("notes", []))
    proj.metadata["imported_from"] = "compatible_json"
    return proj


project_store = ProjectStore()
