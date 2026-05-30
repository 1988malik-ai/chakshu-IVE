# AI-IVE System Architecture

**Author:** Mohit M  
**Version:** 1.0.0  
**Last updated:** 2026-05-29  

---

## 1. Purpose

AI-IVE is a **standalone digital forensic media examination platform** for image and video enhancement, analysis, export, and court-ready documentation. The system separates:

- **Presentation** — React forensic workstation UI  
- **Application API** — FastAPI orchestration layer  
- **Domain engines** — Python processing, FFmpeg, OpenCV/Pillow  
- **Persistence** — Projects, cases, custody, audit logs  

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI-IVE Forensic Workstation                   │
│  (React — ForensicApp.jsx, forensic.css)                         │
│  Command │ Examination │ Custody │ Export │ Reports            │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP /api/*
┌────────────────────────────▼────────────────────────────────────┐
│                    FastAPI Application Layer                       │
│  server.py │ routes_extended.py │ routes_forensics.py           │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Session &     │   │ Forensics     │   │ Export &      │
│ Filters       │   │ Case/Custody  │   │ Reports       │
│ api/session   │   │ forensics/    │   │ export/       │
│ filters/      │   │ project/      │   │ reports/      │
└───────┬───────┘   └───────────────┘   └───────┬───────┘
        │                                        │
        └────────────────┬───────────────────────┘
                         ▼
              ┌─────────────────────┐
              │ FFmpeg / FFprobe    │
              │ OpenCV (optional)   │
              │ Pillow / NumPy      │
              └─────────────────────┘
```

---

## 3. Layer Responsibilities

### 3.1 Presentation Layer (`frontend/`)

| Component | Responsibility |
|-----------|----------------|
| `ForensicApp.jsx` | Forensic workstation shell, navigation, examination workflow |
| `api/client.js` | Typed API client; error parsing |
| `styles/forensic.css` | Dark forensic theme, panels, custody tables |

**Author:** Mohit M — UI structured for examination lab workflows, not consumer editing.

### 3.2 API Layer (`src/aive/api/`)

| Module | Responsibility |
|--------|----------------|
| `server.py` | Core routes: media, filters, license, bookmarks |
| `routes_extended.py` | PDF export, bundles, audio, I-frames, reports |
| `routes_forensics.py` | Cases, custody, non-destructive examination |
| `session.py` | Session state, **master_frame**, filter pipeline |
| `config.py` | Ports, CORS |

### 3.3 Domain — Filters (`src/aive/filters/`)

| Module | Responsibility |
|--------|----------------|
| `catalog.py` | 191 filter definitions (MUST ≥140) |
| `engine.py` | Dispatch to forensic or legacy OpenCV paths |
| `forensic.py` | Deep implementations for examination-grade filters |

**Design note (Mohit M):** Catalog registers all filters; `FORENSIC_FILTER_IDS` marks fully implemented processors. Extending compliance = adding IDs to `forensic.py`.

### 3.4 Domain — Forensics (`src/aive/forensics/`)

| Module | Responsibility |
|--------|----------------|
| `case.py` | Cases, evidence, SHA-256 ingest, chain of custody |
| `audit.py` | Append-only audit JSONL |

### 3.5 Domain — Export (`src/aive/export/`)

| Module | Responsibility |
|--------|----------------|
| `exporter.py` | Video export CFR/VFR, stream copy |
| `pdf_frames.py` | Frame PDF with layout |
| `audio.py` | Audio extraction |
| `i_frames.py` | Intra-frame selective export |
| `media_bundle.py` | Original + processed bundles |

### 3.6 Domain — Analysis & Tracking

| Module | Responsibility |
|--------|----------------|
| `analysis/stream.py` | Timestamps, demux, I/P/B |
| `tracking/tracker.py` | Manual, auto, keyframe tracking persistence |

### 3.7 Cross-Cutting

| Module | Responsibility |
|--------|----------------|
| `license/protection.py` | Standalone license enforcement |
| `project/workflow.py` | Human-readable YAML projects |
| `reports/generator.py` | HTML/PDF/DOCX case reports |
| `logging/operations.py` | Optional file logging |
| `i18n/`, `accessibility/` | SHOULD requirements |

---

## 4. Key Design Decisions (Mohit M)

### 4.1 Non-Destructive Examination

```
master_frame  ──►  filter_chain[]  ──►  displayed frame
     │                    │
     │                    └── Re-render full pipeline on each change
     └── Never modified after ingest
```

Ensures forensic defensibility: enhancements are reproducible from master + documented pipeline.

### 4.2 Evidence Integrity

On ingest: `SHA-256` computed → stored on `EvidenceItem` → custody entry `INGEST`.

### 4.3 Decoder Strategy

Primary: **FFmpeg**. Windows adapters (DirectShow, VfW, QuickTime) delegate to FFmpeg when native bridge unavailable — satisfies MUST with pragmatic fallback.

### 4.4 Packaging

| Target | Mechanism |
|--------|-----------|
| Development | `python -m aive.api.server` + Vite |
| Windows 64 | PyInstaller + Electron (`build/windows/`) |
| Single process | `aive-api --frontend-dist` serves React build |

---

## 5. Planned Modules (Compliance Gap Closure)

```
src/aive/
├── annotations/      # R-083–085: shapes, arrows, grouped tracking
├── audio/
│   ├── player.py     # R-112–117: frame-accurate, multichannel, sync
│   └── redaction.py  # R-114
├── redaction/        # R-163: privacy pixelation
├── overlays/         # R-121–123: timestamp, grid, subtitles
├── comparison/       # R-124–125: side-by-side, PiP
├── measurement/      # R-170–171: scale, speed
├── capture/          # R-180–183: devices, screen capture
├── integration/      # R-194: external metadata tools
└── analysis/
    └── mpeg_viz.py   # R-074: macroblocks, motion vectors
```

---

## 6. Data Flow — Examination

1. User ingests evidence → API stores bytes → hash → custody log  
2. Session loads `master_frame` + display frame  
3. User applies filters → pipeline appended → re-render from master  
4. Workflow steps recorded in project YAML + audit log  
5. Export/report modules read project + case metadata  

---

## 7. Configuration

| File | Purpose |
|------|---------|
| `config/app.yaml` | Ports, trial days, decoder default |
| `~/.ai-ive/` | License, bookmarks, cases, audit log |

---

## 8. Dependencies

| Dependency | Role |
|------------|------|
| FastAPI / Uvicorn | API server |
| React / Vite | Forensic UI |
| FFmpeg / FFprobe | Video/audio MUST requirements |
| OpenCV (optional) | Filters, tracking |
| reportlab, python-docx | PDF/DOC reports |
| cryptography | License |

---

## 9. Author & Maintenance

**Architecture owner:** Mohit M  

Change control: update `REQUIREMENTS-COMPLIANCE.md` when modules move from PLANNED → IMPLEMENTED.

---

*End of architecture document.*
