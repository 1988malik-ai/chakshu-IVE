# Chakshu — Windows installable package

**Simplest way to run on Windows:** see **[WINDOWS-QUICKSTART.md](WINDOWS-QUICKSTART.md)** — double-click `Setup-Chakshu.bat` once, then `Run-Chakshu.bat`.

---

Build a **single setup `.exe`** on a Windows PC. End users only run the installer — no Python, Node, or FFmpeg install required (FFmpeg is bundled via `imageio-ffmpeg`).

---

## What you need (build machine only)

| Tool | Version | Download |
|------|---------|----------|
| **Windows** | 10 or 11 (64-bit) | — |
| **Python** | 3.11, 3.12, or 3.13 | [python.org](https://www.python.org/downloads/) — tick **Add python.exe to PATH** |
| **Node.js** | LTS | [nodejs.org](https://nodejs.org/) |

Optional: **Git** to clone the repo.

---

## Simplest build (3 steps)

### 1. Get the project

```powershell
cd $env:USERPROFILE\Desktop
# unzip or git clone AI-IVE folder here
cd AI-IVE
```

### 2. One-time setup + build

**Double-click** `Build-Chakshu.bat` in the project folder.

Or in PowerShell:

```powershell
.\scripts\build_windows.ps1
```

First run installs Python deps (~2–5 min), then builds the UI, backend `.exe`, and NSIS installer (~5–15 min total).

### 3. Ship the installer

Output file:

```text
desktop\dist\Chakshu-Setup-1.0.0.exe
```

Copy to any Windows PC → run → **Chakshu Forensics** appears in Start Menu and Desktop.

---

## Build options

```powershell
# Skip venv recreate if already installed
.\scripts\build_windows.ps1 -SkipInstall

# Backend only (no Electron) — for testing or IT-managed browser access
.\scripts\build_windows.ps1 -ApiOnly
# Then: cd dist-backend; .\aive-api.exe --frontend-dist .\frontend-dist
# Open http://127.0.0.1:9450
```

---

## Development on Windows (without building installer)

```powershell
.\scripts\install.ps1 -y

# Terminal 1 — API
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "src"
python -m aive.api.server

# Terminal 2 — UI
cd frontend
npm install
npm run dev
# Open http://localhost:9451

# Terminal 3 — optional native window
cd desktop
npm install
npm start
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` not found | Reinstall Python with **Add to PATH**, or use `py -3.12` |
| PyInstaller fails on OpenCV | Use Python **3.12** (not 3.14) |
| `npm` not found | Install Node.js LTS and restart terminal |
| SmartScreen warning | Normal for unsigned builds; click **More info → Run anyway**, or code-sign the installer for production |
| Video decode fails after install | Rebuild with `requirements-video.txt` installed (included in `install.ps1`) |
| Blank window after install | Rebuild with latest `scripts/build_windows.ps1` (frontend path fix) |

---

## What gets packaged

```text
Chakshu-Setup-1.0.0.exe
  └── Chakshu Forensics (Electron)
        ├── main.js / native window
        └── resources/backend/
              ├── aive-api.exe      ← Python API + OpenCV + FFmpeg
              └── frontend-dist/    ← React UI
```

At launch, Electron starts `aive-api.exe`, waits for `/api/health`, then opens the UI at `http://127.0.0.1:9450`.

---

## Production notes

- **Code signing** — set a certificate in electron-builder for enterprise deployment (currently unsigned).
- **Updates** — bump `version` in `desktop/package.json` and `pyproject.toml` before each release.
- **Smaller build** — `-ApiOnly` skips Electron (~150 MB smaller); users open the app in Edge/Chrome.

See also: [`desktop/README.md`](../desktop/README.md) · [`FFMPEG-CROSS-PLATFORM.md`](FFMPEG-CROSS-PLATFORM.md)
