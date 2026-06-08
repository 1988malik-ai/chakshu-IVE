# Chakshu on Windows — simplest setup

## Native app (no setup, no browser)

Double-click **`Chakshu-Native-1.0.0.exe`** → opens in its own Windows window.

How to get it: **[`WINDOWS-EXTRACT-AND-RUN.md`](WINDOWS-EXTRACT-AND-RUN.md)**

Browser mode: unzip **`Chakshu-Portable.zip`** → **`Run-Chakshu.bat`**

---

## Dev setup (edit code / build installer)

Two `.bat` files in the project folder. No Mac, no Docker.

---

## Before you start (install once on the PC)

1. Double-click **`Install-Prerequisites.bat`** (installs Python 3.12 + Node via winget)  
   Or manual steps: [`COPY-TO-WINDOWS.md`](COPY-TO-WINDOWS.md#install-python--node-on-windows-once-per-pc)  
   If the zip has `frontend/dist/`, you can use `Install-Prerequisites.bat -SkipNode` (Python only).

3. Copy or unzip the **AI-IVE** project folder (e.g. `Desktop\AI-IVE`).

**Faster setup:** On Mac first, run `./scripts/prefetch_windows_assets.sh`, then copy the whole folder to Windows (cached wheels + pre-built UI). See [`WINDOWS-OFFLINE-CACHE.md`](WINDOWS-OFFLINE-CACHE.md).

---

## Run Chakshu (every time)

| Step | Action |
|------|--------|
| **Once** | Double-click **`Setup-Chakshu.bat`** (~3–5 min first time) |
| **Daily** | Double-click **`Run-Chakshu.bat`** |

Browser opens at **http://localhost:9451**

To stop: close the black **Run-Chakshu** window (and the small minimized API window if still open).

---

## Optional: ship a Windows installer (.exe)

On a Windows PC, after setup works:

1. Double-click **`Build-Chakshu.bat`** (~10–15 min).
2. Send users: `desktop\dist\Chakshu-Setup-1.0.0.exe`  
   They do **not** need Python or Node.

Details: [`WINDOWS-INSTALL.md`](WINDOWS-INSTALL.md)

---

## Problems?

| Issue | Fix |
|-------|-----|
| `python` not found | Reinstall Python with **Add to PATH** |
| `npm` not found | Install Node.js LTS, restart PC |
| Setup fails on OpenCV | Use Python **3.12**, not 3.14 |
| Port already in use | Close other Chakshu windows; restart |
| Blank page | Wait 10s; try http://127.0.0.1:9450 |

---

## Manual (PowerShell)

```powershell
cd Desktop\AI-IVE
.\Setup-Chakshu.bat    # or: .\scripts\install.ps1 -y; cd frontend; npm install
.\Run-Chakshu.bat
```
