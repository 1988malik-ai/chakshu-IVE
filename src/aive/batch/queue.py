"""Batch conversion queue — multiple files and folders."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from aive.export.exporter import ExportOptions, VideoExporter


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchJob:
    input_path: Path
    output_path: Path
    options: ExportOptions
    status: JobStatus = JobStatus.PENDING
    error: str = ""
    progress: float = 0.0


@dataclass
class BatchQueue:
    jobs: list[BatchJob] = field(default_factory=list)
    _exporter: VideoExporter = field(default_factory=VideoExporter)

    def add_file(self, input_path: Path, output_path: Path, options: ExportOptions) -> BatchJob:
        job = BatchJob(input_path=input_path, output_path=output_path, options=options)
        self.jobs.append(job)
        return job

    def add_folder(
        self,
        folder: Path,
        output_dir: Path,
        options_factory: Callable[[Path], ExportOptions],
        extensions: set[str] | None = None,
    ) -> list[BatchJob]:
        extensions = extensions or {
            ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".mxf", ".ts", ".m4v"
        }
        added = []
        for path in sorted(folder.rglob("*")):
            if path.is_file() and path.suffix.lower() in extensions:
                rel = path.relative_to(folder)
                out = output_dir / rel.with_suffix(options_factory(path).output_path.suffix)
                out.parent.mkdir(parents=True, exist_ok=True)
                job = self.add_file(path, out, options_factory(path))
                added.append(job)
        return added

    def run_all(self, on_progress: Callable[[BatchJob], None] | None = None) -> dict[str, Any]:
        results = {"done": 0, "failed": 0, "jobs": []}
        for job in self.jobs:
            if job.status == JobStatus.CANCELLED:
                continue
            job.status = JobStatus.RUNNING
            if on_progress:
                on_progress(job)
            result = self._exporter.export(job.input_path, job.options)
            if result.get("success"):
                job.status = JobStatus.DONE
                job.progress = 1.0
                results["done"] += 1
            else:
                job.status = JobStatus.FAILED
                job.error = result.get("stderr", "Unknown error")
                results["failed"] += 1
            results["jobs"].append(
                {"input": str(job.input_path), "status": job.status.value, "error": job.error}
            )
        return results
