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

## Windows .exe (later)

1. Build React: `cd frontend && npm run build`
2. Package Python API with PyInstaller (`scripts/build_windows.ps1`)
3. Build Electron installer: `cd desktop && npm run build`

Details: `desktop/README.md`

Development desktop shell (native file dialogs):

```bash
# Terminal 1: ./scripts/dev.sh
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
