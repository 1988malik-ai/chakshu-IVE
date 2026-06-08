# Pre-build on Mac → faster Windows setup

You **cannot** copy a Mac `.venv` or Mac `node_modules` to Windows — native packages (OpenCV, etc.) are platform-specific.

You **can** prepare two portable assets on Mac and copy the project folder to Windows.

---

## What works vs what does not

| Asset | Mac → Windows? | Notes |
|-------|----------------|-------|
| `.venv/` from Mac | **No** | Wrong CPU/OS binaries |
| `node_modules/` from Mac | **No** | Native addons break |
| `frontend/dist/` | **Yes** | Static HTML/JS — skip npm on Windows |
| `packaging/wheels/win-py312/` | **Yes** | Windows `.whl` files — offline pip |
| `Chakshu-Setup.exe` | Build on **Windows or GitHub Actions** | Cannot build `.exe` on Mac |

---

## Recommended workflow

### On your Mac (once per release)

```bash
cd ~/Desktop/AI-IVE
chmod +x scripts/prefetch_windows_assets.sh
./scripts/prefetch_windows_assets.sh
```

This creates:

- `packaging/wheels/win-py312/` — Windows Python packages (~200–400 MB)
- `frontend/dist/` — built UI

Zip the **AI-IVE** folder (USB, cloud, network share) and copy to Windows.

### On Windows

1. Unzip the folder.
2. Install **Python 3.12** + **Node.js** only if you use **dev mode** without `frontend/dist`.
3. Double-click **`Setup-Chakshu.bat`** — pip uses cached wheels (much faster, works offline).
4. Double-click **`Run-Chakshu.bat`** — if `frontend/dist` exists, **no npm**; opens http://127.0.0.1:9450.

---

## Fastest for end users (no Python on Windows)

Skip dev setup entirely:

1. On Mac: push code to GitHub → **Actions** → **Build Windows installer** → download artifact.  
   Or build on a Windows PC: `Build-Chakshu.bat`.
2. Give users **`Chakshu-Setup-1.0.0.exe`** only.

They install once; no Python, Node, or wheel cache needed.

---

## Wheels only (Mac command)

```bash
./scripts/cache_windows_wheels.sh
```

Requires network on Mac. Re-run when `requirements-*.txt` changes.

---

## Size tip

`packaging/wheels/` is large — add to `.gitignore`; distribute via zip/USB, not git.
