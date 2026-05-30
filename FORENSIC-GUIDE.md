# AI-IVE Forensics — Examination Guide

## Purpose

AI-IVE is structured for **digital forensic media examination**:

- **Non-destructive enhancement** — original evidence preserved (`master_frame`); filters re-render from master
- **Chain of custody** — ingest logged with SHA-256
- **I-frame export** — selective intra-coded frame extraction
- **Stream analysis** — I / P / B frame counts
- **Legal export** — PDF frame sheets, audio extraction, original + processed bundles
- **Case reports** — HTML, PDF, DOCX with workflow steps and settings

## Run

```bash
# Terminal 1
cd ~/Desktop/AI-IVE
source .venv/bin/activate
export PYTHONPATH=src
pip install -r requirements-minimal.txt
python -m aive.api.server

# Terminal 2
cd frontend && npm run dev
```

Open **http://localhost:9451**

## Workflow

1. **Ingest Evidence** — uploads file, computes hash, adds custody entry
2. **Examination Lab** — apply **FORENSIC** filters (30+ implemented); pipeline stacks on master
3. **Reset to Original** — clears enhancement chain
4. **Analyze I/P/B** — enter full video path
5. **Chain of Custody** — view ingest/enhance log
6. **Legal Export** — I-frames, audio, PDF, bundles
7. **Case Reports** — automated documentation

## Filters

- **FORENSIC** badge = implemented (visible change)
- **CAT** = catalog entry (future work)

Filters chain together: each Apply adds to pipeline and re-renders from **original master**.

## Requirements

- **FFmpeg** for video/audio/I-frame: `brew install ffmpeg`
- **OpenCV** recommended for full filter set: `pip install opencv-python-headless`
