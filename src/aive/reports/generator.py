"""Automated reports — HTML, PDF, DOC with templates and paper sizes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from aive.project.workflow import AiveProject, WorkflowStep


@dataclass
class ReportSettings:
    paper_size: str = "A4"  # A4, Letter, Legal, A3
    orientation: str = "portrait"
    template: str = "standard"  # standard | detailed | executive | minimal
    title: str = "Chakshu Processing Report"
    author: str = ""
    include_steps: bool = True
    include_settings: bool = True
    include_references: bool = True
    output_formats: list[str] = field(default_factory=lambda: ["html"])


TEMPLATES = {
    "standard": {"accent": "#1e40af", "header_bg": "#f1f5f9"},
    "detailed": {"accent": "#0f766e", "header_bg": "#ecfdf5"},
    "executive": {"accent": "#4c1d95", "header_bg": "#f5f3ff"},
    "minimal": {"accent": "#374151", "header_bg": "#ffffff"},
}


def generate_report(
    project: AiveProject,
    output_dir: Path,
    settings: ReportSettings | None = None,
) -> dict[str, Any]:
    settings = settings or ReportSettings()
    output_dir.mkdir(parents=True, exist_ok=True)
    tpl = TEMPLATES.get(settings.template, TEMPLATES["standard"])
    outputs = []

    if "html" in settings.output_formats:
        html_path = output_dir / f"report_{project.project_id[:8]}.html"
        html_path.write_text(_render_html(project, settings, tpl), encoding="utf-8")
        outputs.append({"format": "html", "path": str(html_path)})

    if "pdf" in settings.output_formats:
        pdf_path = output_dir / f"report_{project.project_id[:8]}.pdf"
        pdf_result = _render_pdf(project, settings, tpl, pdf_path)
        if pdf_result.get("success"):
            outputs.append({"format": "pdf", "path": str(pdf_path)})

    if "doc" in settings.output_formats or "docx" in settings.output_formats:
        doc_path = output_dir / f"report_{project.project_id[:8]}.docx"
        doc_result = _render_docx(project, settings, doc_path)
        if doc_result.get("success"):
            outputs.append({"format": "docx", "path": str(doc_path)})
        else:
            rtf = output_dir / f"report_{project.project_id[:8]}.rtf"
            rtf.write_text(_render_rtf(project, settings), encoding="utf-8")
            outputs.append({"format": "rtf", "path": str(rtf), "note": "docx_unavailable"})

    return {"success": bool(outputs), "outputs": outputs, "paper_size": settings.paper_size}


def _render_html(project: AiveProject, settings: ReportSettings, tpl: dict) -> str:
    steps_html = ""
    for i, step in enumerate(project.workflow_steps, 1):
        refs = ", ".join(step.references) if step.references else "—"
        settings_json = str(step.settings) if settings.include_settings else ""
        steps_html += f"""
        <tr>
          <td>{i}</td>
          <td>{step.timestamp}</td>
          <td><strong>{step.action}</strong></td>
          <td><code>{settings_json}</code></td>
          <td>{refs if settings.include_references else ''}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{settings.title}</title>
<style>
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; margin: 40px; color: #1e293b; }}
  h1 {{ color: {tpl['accent']}; border-bottom: 3px solid {tpl['accent']}; padding-bottom: 8px; }}
  .meta {{ background: {tpl['header_bg']}; padding: 16px; border-radius: 8px; margin: 20px 0; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  th {{ background: {tpl['accent']}; color: white; text-align: left; padding: 10px; }}
  td {{ border-bottom: 1px solid #e2e8f0; padding: 8px; font-size: 14px; }}
  .footer {{ margin-top: 40px; font-size: 12px; color: #64748b; }}
</style></head><body>
<h1>{settings.title}</h1>
<div class="meta">
  <p><strong>Project:</strong> {project.name}</p>
  <p><strong>ID:</strong> {project.project_id}</p>
  <p><strong>Paper:</strong> {settings.paper_size} ({settings.orientation})</p>
  <p><strong>Template:</strong> {settings.template}</p>
  <p><strong>Generated:</strong> {datetime.utcnow().isoformat()}Z</p>
  {f'<p><strong>Author:</strong> {settings.author}</p>' if settings.author else ''}
</div>
<h2>Workflow Steps</h2>
<table>
  <tr><th>#</th><th>Time</th><th>Action</th><th>Settings</th><th>References</th></tr>
  {steps_html or '<tr><td colspan="5">No steps recorded</td></tr>'}
</table>
<h2>Filter Pipeline</h2>
<pre>{project.filter_pipeline}</pre>
<div class="footer">AI-IVE Automated Report — Confidential</div>
</body></html>"""


def _render_pdf(project: AiveProject, settings: ReportSettings, tpl: dict, path: Path) -> dict:
    try:
        from reportlab.lib.pagesizes import A3, A4, letter, legal, landscape
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
    except ImportError:
        return {"success": False, "error": "reportlab not installed"}

    sizes = {"A4": A4, "Letter": letter, "Legal": legal, "A3": A3}
    page = sizes.get(settings.paper_size, A4)
    if settings.orientation == "landscape":
        page = landscape(page)

    c = canvas.Canvas(str(path), pagesize=page)
    w, h = page
    y = h - 20 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, settings.title)
    y -= 10 * mm
    c.setFont("Helvetica", 10)
    for line in [
        f"Project: {project.name}",
        f"Paper: {settings.paper_size}",
        f"Steps: {len(project.workflow_steps)}",
    ]:
        y -= 6 * mm
        c.drawString(20 * mm, y, line)
    y -= 10 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "Processing Steps")
    y -= 8 * mm
    c.setFont("Helvetica", 9)
    for i, step in enumerate(project.workflow_steps[:40], 1):
        if y < 20 * mm:
            c.showPage()
            y = h - 20 * mm
        text = f"{i}. [{step.timestamp}] {step.action}"
        c.drawString(20 * mm, y, text[:90])
        y -= 5 * mm
    c.save()
    return {"success": True}


def _render_docx(project: AiveProject, settings: ReportSettings, path: Path) -> dict:
    try:
        from docx import Document
        from docx.shared import Inches, Pt
    except ImportError:
        return {"success": False, "error": "python-docx not installed"}

    doc = Document()
    doc.add_heading(settings.title, 0)
    doc.add_paragraph(f"Project: {project.name}")
    doc.add_paragraph(f"Paper size: {settings.paper_size}")
    doc.add_paragraph(f"Generated: {datetime.utcnow().isoformat()}Z")
    doc.add_heading("Workflow Steps", level=1)
    table = doc.add_table(rows=1, cols=4)
    hdr = table.rows[0].cells
    hdr[0].text = "#"
    hdr[1].text = "Time"
    hdr[2].text = "Action"
    hdr[3].text = "Settings"
    for i, step in enumerate(project.workflow_steps, 1):
        row = table.add_row().cells
        row[0].text = str(i)
        row[1].text = step.timestamp
        row[2].text = step.action
        row[3].text = str(step.settings)
    doc.save(str(path))
    return {"success": True}


def _render_rtf(project: AiveProject, settings: ReportSettings) -> str:
    lines = [r"{\rtf1\ansi", r"\b " + settings.title + r"\b0\par"]
    for step in project.workflow_steps:
        lines.append(f"{step.action} - {step.timestamp}\\par")
    lines.append("}")
    return "\n".join(lines)
