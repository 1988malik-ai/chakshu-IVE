# Minimum files to copy to Windows

## Simplest: native Windows app (recommended)

Copy **one file**: **`Chakshu-Native-1.0.0.exe`** — double-click → native window, no browser.

1. Get it from **GitHub Actions** artifact **`Chakshu-Native`**, or run **`Build-Native.bat`** once on a Windows PC.
2. Send that `.exe` to any Windows PC.

**Browser mode** (zip + `Run-Chakshu.bat`): artifact **`Chakshu-Portable`**.

Full guide: **[`WINDOWS-EXTRACT-AND-RUN.md`](WINDOWS-EXTRACT-AND-RUN.md)**

---

## Dev setup (only if you edit code)

Copy **one zip** made on Mac with `scripts/pack_for_windows.sh` — or copy the folders below manually.

**Do not copy:** `.venv/`, `node_modules/`, `.git/`, `dist/`, `dist-backend/`, `build/`

---

## Install Python + Node on Windows (once per PC)

### One-click installer (recommended)

Double-click **`Install-Prerequisites.bat`** in the project folder (single file — no extra scripts needed).

- Installs **Python 3.12** and **Node.js LTS** via `winget`
- Requires Windows 10/11 with **App Installer** (winget)
- If prompted, allow **Administrator** access
- After it finishes, **close all terminals**, then run **`Setup-Chakshu.bat`**

Python only (pre-built `frontend/dist/` in zip — no Node needed):

```cmd
Install-Prerequisites.bat -SkipNode
```

Manual commands (same as the `.bat` file):

```cmd
winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
```

---

### Python 3.12 — **required** (manual install)

1. Download: https://www.python.org/downloads/release/python-3120/  
   (Windows installer — **64-bit**)
2. Run the installer.
3. On the first screen, check **“Add python.exe to PATH”** (bottom of the window).
4. Click **Install Now** (default options are fine).
5. Close and reopen any Command Prompt / PowerShell windows after install.
6. Verify in a new terminal:

```cmd
python --version
```

Expected: `Python 3.12.x`

If you see “python is not recognized”, reinstall Python and ensure **Add to PATH** was checked.

**Alternative (winget):**

```cmd
winget install Python.Python.3.12
```

---

### Node.js LTS — **optional to run**, **required to build `.exe`**

| Scenario | Need Node? |
|----------|------------|
| Zip includes `frontend/dist/` (Mac prefetch) | **No** — `Setup-Chakshu.bat` skips npm |
| No pre-built UI, or you run `Build-Chakshu.bat` | **Yes** |

1. Download: https://nodejs.org/ (choose **LTS**)
2. Run the installer — accept defaults (includes npm).
3. Restart the terminal (or reboot if `npm` is not found).
4. Verify:

```cmd
node --version
npm --version
```

**Alternative (winget):**

```cmd
winget install OpenJS.NodeJS.LTS
```

---

## Goal A — Run Chakshu (dev / daily use)

| Copy | Required? |
|------|-----------|
| `Setup-Chakshu.bat`, `Run-Chakshu.bat`, `Install-Prerequisites.bat` | ✅ |
| `scripts/install.ps1`, `scripts/install_prerequisites.ps1`, `scripts/run_windows.ps1`, `scripts/check-media-deps.py` | ✅ |
| `src/` | ✅ |
| `config/` | ✅ |
| `requirements-fast.txt`, `requirements-video.txt`, `requirements-reports.txt` | ✅ |
| `pyproject.toml` | ✅ |
| `frontend/package.json` + `frontend/src/` + `frontend/public/` + `frontend/index.html` + `frontend/vite.config.js` | ✅ *or* skip if you include `frontend/dist/` |
| `frontend/dist/` | ✅ if pre-built on Mac (then **no Node.js** on Windows) |
| `packaging/wheels/win-py312/` | Optional — faster offline `Setup-Chakshu.bat` |

**Windows installs:** Python 3.12 only (Node optional if `frontend/dist` included).

---

## Goal B — Build installer `.exe` on Windows

Everything in **Goal A**, plus:

| Copy | Required? |
|------|-----------|
| `Build-Chakshu.bat` | ✅ |
| `scripts/build_windows.ps1`, `scripts/aive-api.spec` | ✅ |
| `desktop/main.js`, `desktop/preload.js`, `desktop/package.json` | ✅ |
| Full `frontend/` source (build re-runs `npm run build`) | ✅ unless `frontend/dist` already present |

**Windows installs:** Python 3.12 + Node.js LTS.

**Output:** `desktop\dist\Chakshu-Setup-1.0.0.exe` — only this file needed on other PCs.

---

## Smallest copy (Mac prep → Windows run only)

On Mac:

```bash
./scripts/prefetch_windows_assets.sh   # wheels + frontend/dist
./scripts/pack_for_windows.sh          # creates chakshu-windows-port.zip
```

On Windows:

1. Double-click **`Install-Prerequisites.bat`** (or install Python/Node manually — see above)
2. Unzip `chakshu-windows-port.zip` (e.g. `Desktop\AI-IVE`)
3. Double-click **`Setup-Chakshu.bat`** (once)
4. Double-click **`Run-Chakshu.bat`** (each time)

~250–500 MB zip (mostly wheels).

More detail: [`WINDOWS-QUICKSTART.md`](WINDOWS-QUICKSTART.md)
