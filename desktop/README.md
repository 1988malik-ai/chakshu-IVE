# AI-IVE Desktop (Electron → Windows .exe)

Electron loads the **React** app and runs the **Python API** as a subprocess (production) or connects to dev servers (development).

## Development

**Terminal 1** — API + React:

```bash
cd ~/Desktop/AI-IVE
./scripts/dev.sh
```

**Terminal 2** — Electron window:

```bash
cd desktop
npm install
npm start
```

Electron opens http://localhost:9451 and exposes `window.aiveDesktop.openFile()` for native file pickers.

## Production build (Windows)

Prerequisites: Node.js, Python venv with deps, FFmpeg on target machines.

```powershell
cd $env:USERPROFILE\Desktop\AI-IVE
.\scripts\build_windows.ps1
```

Output: `desktop\dist\AI-IVE-Setup-1.0.0.exe`

### What gets packaged

1. `frontend/dist` — built React static files  
2. `dist-backend/aive-api.exe` — PyInstaller bundle of FastAPI + OpenCV + core  
3. Electron shell — native window, file dialogs  

## Alternative: API-only desktop

Serve React from Python (single process, no Electron):

```bash
cd frontend && npm run build
aive-api --frontend-dist ./frontend/dist
```

Open http://127.0.0.1:9450 — suitable for PyInstaller-only `.exe` with embedded UI.
