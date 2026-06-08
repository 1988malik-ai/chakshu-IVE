# Mac development — Docker vs Windows `.exe`

You **cannot** run a real Windows environment inside Docker on Mac. You **can** run Chakshu in a **Linux container** on Mac, or build the Windows installer **in the cloud** without a Windows PC.

---

## Quick comparison

| Approach | Works on Mac? | Produces Windows `.exe`? | Best for |
|----------|---------------|---------------------------|----------|
| **Native dev** (`install.sh` + `dev.sh`) | Yes | No | Daily development |
| **Docker** (`docker compose up`) | Yes | No | Same app, isolated deps, demos |
| **Windows VM** (Parallels / UTM / VMware) | Yes (slow) | Yes | Local `.exe` build + Windows QA |
| **GitHub Actions** (`build-windows.yml`) | Yes (trigger from Mac) | Yes | `.exe` without owning Windows |
| **Docker “Windows container”** | **No** | — | Not supported on Mac Docker |

---

## Option A — Docker on Mac (recommended for “installable” on Mac/Linux)

One container: API + React UI on port **9450**.

```bash
cd ~/Desktop/AI-IVE
mkdir -p chakshu-data    # optional: evidence/export mount
docker compose up --build
```

Open **http://localhost:9450**

Stop: `Ctrl+C` or `docker compose down`

### Mount your evidence folder

```bash
export CHAKSHU_DATA=$HOME/Desktop/chakshu-test-data
docker compose up --build
```

Inside the app, use paths under `/data/...` when loading by full path (container filesystem).

### Limits

- Not a Windows `.exe` — it is a **Linux** image.
- GPU encoding may differ from native Mac/Windows.
- File dialogs use browser upload, not native Windows pickers.

---

## Option B — Build Windows `.exe` from Mac (no Windows PC)

Use **GitHub Actions** (real Windows runner):

1. Push the repo to GitHub (or use a fork).
2. **Actions** → **Build Windows installer** → **Run workflow** (or push to `main`).
3. When finished, download artifact **Chakshu-Windows-Setup** (`.exe`).

Workflow file: `.github/workflows/build-windows.yml`

Same steps as `scripts/build_windows.ps1`, but runs on `windows-latest`.

---

## Option C — Windows VM on Mac (full simulation)

If you need to test the installer or Electron app locally:

| Tool | Notes |
|------|--------|
| [UTM](https://mac.getutm.app/) | Free, Apple Silicon + Intel |
| Parallels / VMware Fusion | Paid, good performance |
| Microsoft Dev Drive / Windows 11 ARM | On M1/M2/M3 Mac |

Inside the VM:

1. Install Python 3.12 + Node.js LTS.
2. Copy or clone the project.
3. Run `Build-Chakshu.bat` or `.\scripts\build_windows.ps1`.

This is the only way to **fully simulate** Windows UI behavior on Mac.

---

## Option D — What does *not* work

| Idea | Why |
|------|-----|
| `docker run mcr.microsoft.com/windows/...` on Mac | Windows containers require a Windows host |
| Wine / CrossOver for the build | PyInstaller + Electron + NSIS are unreliable |
| Building `Chakshu-Setup.exe` on macOS directly | PyInstaller output is OS-specific |

---

## Recommended workflow on Mac

```text
Daily work     →  ./scripts/install.sh && ./scripts/dev.sh
Demo / CI box  →  docker compose up --build
Ship Windows   →  GitHub Actions artifact OR Windows VM build
```

---

## Troubleshooting Docker

| Issue | Fix |
|-------|-----|
| Build slow first time | Normal — pulls Node + Python images |
| Port 9450 in use | Change mapping: `"9451:9450"` in `docker-compose.yml` |
| OpenCV errors in container | Rebuild: `docker compose build --no-cache` |
| Video/ffmpeg | Bundled via `imageio-ffmpeg` in image |

See also: [`WINDOWS-INSTALL.md`](WINDOWS-INSTALL.md) · [`../docker-compose.yml`](../docker-compose.yml)
