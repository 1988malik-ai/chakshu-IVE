"""Assemble report data from project, case, and optional bookmarks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from aive.project.workflow import AiveProject, WorkflowStep


@dataclass
class ReportContext:
    project: AiveProject
    case: dict[str, Any] | None = None
    bookmarks: list[dict[str, Any]] | None = None

    def step_rows(self, *, include_settings: bool = True, include_references: bool = True) -> list[dict[str, str]]:
        rows = []
        for i, step in enumerate(self.project.workflow_steps, 1):
            rows.append(
                {
                    "index": str(i),
                    "timestamp": step.timestamp,
                    "action": step.action,
                    "settings": format_settings(step) if include_settings else "",
                    "references": format_references(step) if include_references else "",
                    "notes": step.notes or "",
                }
            )
        return rows

    def pipeline_summary(self) -> str:
        if not self.project.filter_pipeline:
            return "—"
        lines = []
        for i, entry in enumerate(self.project.filter_pipeline, 1):
            fid = entry.get("filter_id", entry) if isinstance(entry, dict) else str(entry)
            params = entry.get("params", {}) if isinstance(entry, dict) else {}
            lines.append(f"{i}. {fid}" + (f" ({json.dumps(params, default=str)})" if params else ""))
        return "\n".join(lines)


def format_settings(step: WorkflowStep) -> str:
    if not step.settings:
        return "—"
    try:
        return json.dumps(step.settings, indent=2, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(step.settings)


def format_references(step: WorkflowStep) -> str:
    if not step.references:
        return "—"
    return "; ".join(str(r) for r in step.references)


def build_context(
    project: AiveProject,
    *,
    case: dict[str, Any] | None = None,
    bookmarks: list[dict[str, Any]] | None = None,
) -> ReportContext:
    return ReportContext(project=project, case=case, bookmarks=bookmarks or [])
