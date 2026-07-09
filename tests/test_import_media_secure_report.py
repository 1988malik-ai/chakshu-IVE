import json
from pathlib import Path

from aive.forensics.secure_copy import secure_copy
from aive.media.capabilities import media_format_capabilities
from aive.project.workflow import AiveProject, inspect_compatible_project
from aive.reports.generator import ReportSettings, generate_report


def test_project_import_inspection_reports_counts(tmp_path: Path):
    project_path = tmp_path / "case.aive.json"
    project_path.write_text(
        json.dumps(
            {
                "aive_project": {
                    "name": "Imported Case",
                    "media": [{"path": "sample.jpg"}],
                    "filter_pipeline": [{"id": "brightness"}],
                    "workflow_steps": [{"action": "load_media", "timestamp": "now"}],
                    "bookmarks": [{"label": "frame"}],
                    "examination_notes": [{"body": "note"}],
                }
            }
        ),
        encoding="utf-8",
    )

    summary = inspect_compatible_project(project_path)

    assert summary["supported"] is True
    assert summary["format"] == "aive_json"
    assert summary["name"] == "Imported Case"
    assert summary["counts"] == {"media": 1, "filters": 1, "steps": 1, "bookmarks": 1, "notes": 1}


def test_media_format_capabilities_shape():
    caps = media_format_capabilities()

    assert ".jpg" in caps["standard_images"]
    assert ".dng" in caps["raw"]["extensions"]
    assert ".mp4" in caps["video"]["extensions"]
    assert "ffmpeg" in caps["video"]["ffmpeg"]


def test_secure_copy_returns_report_path(tmp_path: Path):
    source = tmp_path / "evidence.bin"
    dest = tmp_path / "secure" / "evidence.bin"
    report = tmp_path / "copy-report.json"
    source.write_bytes(b"evidence")

    result = secure_copy(source, dest, report)

    assert result["success"] is True
    assert result["verified"] is True
    assert result["destination"] == str(dest.resolve())
    assert result["report_path"] == str(report)
    assert report.exists()


def test_report_includes_secure_copy_section(tmp_path: Path):
    project = AiveProject(name="Secure Report")
    project.add_step(
        "secure_copy",
        settings={
            "source": "/case/source.mp4",
            "destination": "/case/secure/source.mp4",
            "report_path": "/case/reports/copy-report.json",
            "verified": True,
        },
    )

    result = generate_report(project, tmp_path, ReportSettings(output_formats=["html"]))
    html_path = Path(result["outputs"][0]["path"])
    rendered = html_path.read_text(encoding="utf-8")

    assert "Secure Copy Verification" in rendered
    assert "/case/reports/copy-report.json" in rendered
