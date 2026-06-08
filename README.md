# Chakshu — Digital Media Examination Platform

Professional image and video forensic examination with **191 filters**, license protection, GPU encoding, and live capture.

## Architecture (React + Python)

| Layer | Location | Purpose |
|-------|----------|---------|
| **React UI** | `frontend/` | Vite + React — all screens, filters, preview |
| **Python API** | `src/aive/api/` | FastAPI — processing, export, license, analysis |
| **Core engine** | `src/aive/` | Filters, FFmpeg, GPU, tracking, bookmarks |
| **Desktop .exe** | `desktop/` | Electron wraps React + bundles Python backend |

The old **PyQt6** UI is still available as optional legacy: `pip install -e ".[ui-legacy]"` then `python -m aive.main`.

---

## Quick Start (React — recommended)

### Install (use Python 3.12 — avoid 3.14)

**Python 3.14** has no OpenCV wheel; `pip` will compile from source for 30–60+ minutes. Use **3.11, 3.12, or 3.13** instead.

```bash
cd ~/Desktop/AI-IVE
./scripts/install.sh -y
```

Takes about **1–3 minutes** on Python 3.12 (wheels only). Skips heavy ONNX unless you ask for it.

If install is **still slow**, you are probably on **Python 3.14** or compiling OpenCV — use 3.12:

```bash
rm -rf .venv
brew install python@3.12
./scripts/install.sh -y
```

Optional (large, slow): `pip install -r requirements-ai.txt`

### Terminal 1 — Python API

```bash
source .venv/bin/activate
export PYTHONPATH=src
python -m aive.api.server
```

API: http://127.0.0.1:9450/docs

### Terminal 2 — React UI

```bash
cd ~/Desktop/AI-IVE/frontend
npm install
npm run dev
```

**Open the UI:** http://localhost:9451

**Requirements testing:** [`docs/REQUIREMENTS-TEST-GUIDE.md`](docs/REQUIREMENTS-TEST-GUIDE.md) — verify each R-001…R-196 requirement.  
**Workflow testing:** [`docs/WORKFLOW-TEST-GUIDE.md`](docs/WORKFLOW-TEST-GUIDE.md) — end-to-end examiner scenarios (WF-01…WF-12).  
**Checklist / smoke:** [`docs/REQUIREMENTS-TEST-CHECKLIST.md`](docs/REQUIREMENTS-TEST-CHECKLIST.md) · `./scripts/run-requirements-smoke.sh`

Or use one script:

```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

---

## Ports (default)

| Service | Port | Config |
|---------|------|--------|
| Python API | **9450** | `config/app.yaml` → `server.api_port` |
| React dev UI | **9451** | `config/app.yaml` → `server.frontend_port` |

Override with environment variables:

```bash
export AIVE_API_PORT=9450
export AIVE_FRONTEND_PORT=9451
```

---

## Where is the UI?

| What | Path |
|------|------|
| React app entry | `frontend/src/App.jsx` |
| Styles | `frontend/src/index.css` |
| API client | `frontend/src/api/client.js` |
| Backend routes | `src/aive/api/server.py` |

The UI is **not** shown by running Python alone — you need **both** the API and `npm run dev` (or a built desktop app).

---

## Windows installer

**On a Windows PC** (Python 3.12 + Node.js LTS once):

1. Double-click **`Build-Chakshu.bat`**, or run `.\scripts\build_windows.ps1`
2. Ship **`desktop\dist\Chakshu-Setup-1.0.0.exe`** to users

Full guide: [`docs/WINDOWS-INSTALL.md`](docs/WINDOWS-INSTALL.md) · [`desktop/README.md`](desktop/README.md)

**On Windows:** double-click `Setup-Chakshu.bat` once, then `Run-Chakshu.bat` — see [`docs/WINDOWS-QUICKSTART.md`](docs/WINDOWS-QUICKSTART.md).

**On Mac (no Windows PC):** run in Docker — `docker compose up --build` → http://localhost:9450 — or build the `.exe` via [GitHub Actions](.github/workflows/build-windows.yml). See [`docs/MAC-DOCKER-AND-WINDOWS.md`](docs/MAC-DOCKER-AND-WINDOWS.md).

Development desktop shell (native file dialogs):

```bash
# Terminal 1: ./scripts/dev.sh  (or install.ps1 + dev on Windows)
# Terminal 2:
cd desktop && npm install && npm start
```

---

## License

- **Help → License** in the React UI (or `GET /api/license/status`)
- Generate keys: `python scripts/generate_license.py`

---

## FFmpeg

Required for video export and analysis:

```bash
brew install ffmpeg    # macOS
ffmpeg -version
```

---

## Project layout

```
AI-IVE/
├── frontend/          # React (Vite) — YOUR UI
├── src/aive/api/      # FastAPI backend
├── src/aive/          # Core processing
├── desktop/           # Electron → Windows .exe
├── config/
├── models/            # Custom .onnx
└── scripts/dev.sh     # Run API + React together
```
