# Chakshu Desktop (Electron → Windows installer)

Electron opens a native window; the **Python API** runs as a bundled subprocess with the **React UI** served locally.

## Development

**Terminal 1** — API + React (macOS/Linux):

```bash
cd ~/Desktop/AI-IVE
./scripts/dev.sh
```

**Terminal 2** — Electron:

```bash
cd desktop
npm install
npm start
```

On **Windows**, use `.\scripts\install.ps1` then the same terminals with PowerShell paths (see [`docs/WINDOWS-INSTALL.md`](../docs/WINDOWS-INSTALL.md)).

## Production build (Windows)

**Easiest:** double-click `Build-Chakshu.bat` in the project root.

Or:

```powershell
.\scripts\build_windows.ps1
```

Output: `desktop\dist\Chakshu-Setup-1.0.0.exe`

Full guide: [`docs/WINDOWS-INSTALL.md`](../docs/WINDOWS-INSTALL.md)

### What gets packaged

1. `dist-backend/aive-api.exe` — PyInstaller bundle (FastAPI, OpenCV, FFmpeg)
2. `dist-backend/frontend-dist/` — built React app
3. Electron shell — NSIS installer, Start Menu + desktop shortcut

## Alternative: API-only (no Electron)

Smaller artifact; user opens a browser:

```powershell
.\scripts\build_windows.ps1 -ApiOnly
cd dist-backend
.\aive-api.exe --frontend-dist .\frontend-dist
```

Open http://127.0.0.1:9450
