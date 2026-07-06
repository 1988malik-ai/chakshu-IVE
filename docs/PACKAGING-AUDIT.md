# Packaging Audit — Chakshu Forensics

**Date:** 2026-07-04  
**Scope:** `desktop/`, `packaging/`, `build/`, `Dockerfile`, `docker-compose.yml`, `Run-Chakshu.sh`, `scripts/install.sh`, Windows `*.bat`, quick-start docs cross-check.

---

## Executive summary

Chakshu has **two legitimate port layouts**, not a single universal URL:

| Mode | API | UI | How |
|------|-----|-----|-----|
| **Dev (split)** | `9450` | `9451` | Vite dev server + FastAPI (`scripts/dev.sh`, `Run-Chakshu.sh local/auto` with `.venv`) |
| **Bundled (single)** | `9450` | same port | Built React served by API (`docker compose`, portable `.exe`, pre-built `frontend/dist`) |

Most “9450 vs 9451” confusion comes from **mixing these modes** in docs and install messages, not from wrong runtime wiring. Canonical source of truth: `config/app.yaml` → `server.api_port` / `server.frontend_port`, overridden by `AIVE_API_PORT` / `AIVE_FRONTEND_PORT`.

---

## 1. Quick-start path audit

### `./Run-Chakshu.sh`

| Subcommand | Behavior | URL printed | Verdict |
|------------|----------|-------------|---------|
| `auto` | `.venv` exists → `scripts/dev.sh`; else Docker if available; else minimal install + dev | Dev: 9451 (via `dev.sh`); Docker: 9450 | OK after clarifying Docker message |
| `docker` | `docker compose up --build` | 9450 | **Correct** (bundled UI) |
| `local` | Minimal/full install if needed → `dev.sh` | 9451 | **Correct** |

**Note:** Docker path correctly uses one port. Dev path correctly uses two ports.

### `docker-compose.yml` + `Dockerfile`

- Maps host `9450` → container `9450`.
- `Dockerfile` multi-stage: builds `frontend/dist`, runs `aive.api._launcher` with `--frontend-dist`.
- Healthcheck hits `http://127.0.0.1:9450/api/health`.
- **Verdict:** Consistent bundled mode.

### `scripts/dev.sh`

- Starts API on `AIVE_API_PORT` (default 9450), Vite on `AIVE_FRONTEND_PORT` (default 9451).
- Prints both URLs. Frees both ports before start.
- **Verdict:** Reference implementation for dev mode.

### `scripts/install.sh` (macOS/Linux)

- Full and minimal installs end with `./Run-Chakshu.sh local`.
- Does not hard-code a browser URL.
- **Verdict:** OK.

### `scripts/install.ps1` (Windows)

- **Issue (fixed):** Final message always said `http://localhost:9451` even when `frontend/dist/` exists (Run-Chakshu opens **9450** in pre-built mode).
- **Fix:** Mode-aware completion message.

### `scripts/run_windows.ps1` + `Run-Chakshu.bat`

| Condition | Mode | Browser URL |
|-----------|------|---------------|
| `frontend/dist/index.html` exists | Pre-built UI via `_launcher` | `http://127.0.0.1:9450` |
| No dist | Dev: API + `npm run dev` | `http://localhost:9451` |

- Portable path (`run_portable.ps1`) always uses **9450**.
- `Run-Chakshu.bat` correctly dispatches portable vs dev.
- **Verdict:** Runtime logic correct; docs were stale.

### README.md vs other docs

| Doc / script | Port stated | Accurate for |
|--------------|-------------|--------------|
| `README.md` Quick Start (dev) | API 9450, UI 9451 | Dev |
| `README.md` Mac Docker | 9450 | Bundled |
| `docs/MAC-DOCKER-AND-WINDOWS.md` | 9450 | Bundled |
| `docs/WINDOWS-OFFLINE-CACHE.md` | 9450 (with dist) | Bundled |
| `docs/WINDOWS-QUICKSTART.md` | **Always 9451** | Dev only — **misleading** when `frontend/dist` shipped |
| `docs/WINDOWS-INSTALL.md` | 9451 dev, 9450 packaged | OK |
| `AGENTS.md` | API 9450, UI 9451 | Dev contract (correct) |

---

## 2. Desktop / Electron wrapper audit

### What gets packaged (production)

```
Chakshu-Setup / Chakshu-Native (electron-builder)
├── main.js, preload.js
└── resources/backend/          ← extraResources from dist-backend/
      ├── aive-api.exe          ← PyInstaller; UI embedded in exe (_MEIPASS/frontend-dist)
      └── frontend-dist/        ← redundant copy; launcher prefers in-exe bundle
```

Build pipeline: `scripts/build_windows.ps1` → React build → PyInstaller (`scripts/aive-api.spec`) → stage `dist-backend/` → `desktop/npm run build`.

CI: `.github/workflows/build-windows.yml` produces Setup, Portable zip, and Native exe artifacts.

### Dev vs production behavior (`desktop/main.js`)

| | Dev (`npm start`) | Production (packaged) |
|--|-------------------|------------------------|
| Backend | **Not started** — expects `./scripts/dev.sh` | Spawns `aive-api.exe`, waits for `/api/health` |
| Window URL | `http://localhost:9451` (Vite) | `http://127.0.0.1:9450/` (API static) |
| PYTHONPATH | Set if dev backend were started manually | N/A |

### Gaps vs current React workflow (`ForensicApp`)

| Gap | Severity | Notes |
|-----|----------|-------|
| `window.aiveDesktop.openFile` exposed in `preload.js` but **unused** in `ForensicApp.jsx` | Medium | Electron native file picker not wired; UI uses hidden `<input type="file">` |
| Dev Electron does not auto-start API | Low | Documented in `desktop/README.md`; requires two terminals |
| Legacy `frontend/src/App.jsx` still in tree | Low | `main.jsx` mounts `ForensicApp` — dead code for packaging |
| Windows-only Electron build (`--win --x64`) | Expected | No macOS `.app` / Linux AppImage |
| `desktop/build/icon.png` generated at build time | Low | Missing until `generate_desktop_icon.py` runs |
| UI duplicated in PyInstaller exe **and** `frontend-dist/` folder | Low | Works; external dist is fallback for `--frontend-dist` CLI |
| MJPEG capture uses direct API URL in dev (`client.js`) | OK | Required because Vite proxy breaks multipart streams; bundled mode uses same-origin |

### What Electron bundles well

- Full forensic UI when built (same `ForensicApp` as dev).
- Offline-capable backend with OpenCV, FFmpeg (via PyInstaller + wheels).
- NSIS installer, portable Native exe, and browser portable zip paths.

---

## 3. `packaging/` and `build/` directories

| Path | Purpose | Status |
|------|---------|--------|
| `packaging/wheels/win-py312/` | Offline Windows pip cache (`cache_windows_wheels.sh`) | Populated by prefetch script; referenced by `install.ps1` |
| `desktop/build/` | electron-builder `buildResources` (icon) | Created by `generate_desktop_icon.py` at build time |
| Root `build/` | Not used as primary output | PyInstaller writes to `dist/`; electron-builder output is `desktop/dist/` |

---

## 4. Fixes applied (this audit)

| File | Change |
|------|--------|
| `scripts/install.ps1` | Completion URL now reflects pre-built UI (9450) vs dev UI (9451) |
| `Run-Chakshu.sh` | Docker banner clarifies single-port bundled UI |
| `docker-compose.yml` | Header comment clarifies API serves built React on 9450 |

---

## 5. Recommended packaging improvements (not implemented)

Priority order:

1. **Documentation alignment** — Update `docs/WINDOWS-QUICKSTART.md` to match `run_windows.ps1` dual-mode URLs (Documentation agent).
2. **Wire Electron file dialog** — Call `window.aiveDesktop?.openFile()` from ingest flow when `isElectron` (Frontend + Packaging coordination).
3. **Electron dev ergonomics** — Optionally spawn API subprocess in dev when not already listening (packaging-only change in `main.js`).
4. **Single-port dev option** — `dev.sh --bundled` could build/watch frontend and serve via API (mirrors Docker locally).
5. **macOS desktop target** — Add electron-builder `mac` target + PyInstaller on macOS for internal QA (Windows remains primary ship target).
6. **Version sync** — Single source for version in `pyproject.toml`, `desktop/package.json`, artifact names.
7. **Code signing** — Document or automate Authenticode for enterprise SmartScreen (noted in `WINDOWS-INSTALL.md`).
8. **Trim redundant `frontend-dist/` in NSIS** — Rely on in-exe bundle only to shrink installer (~size TBD).
9. **Health endpoint in Run-Chakshu.bat dev path** — Wait for API before opening browser (mirror `dev.sh` curl loop).

---

## 6. Smoke tests

```bash
# Dev (Mac/Linux)
./Run-Chakshu.sh local
# → http://localhost:9451 (UI), http://127.0.0.1:9450/docs (API)

# Docker
./Run-Chakshu.sh docker
# → http://localhost:9450

# Windows dev (after Setup-Chakshu.bat)
# Run-Chakshu.bat → 9451 if no frontend/dist, else 9450

# Windows portable
# Run-Chakshu.bat in Chakshu-Portable/ → 9450
```

---

## 7. Port reference (quick lookup)

```
config/app.yaml          api_port: 9450, frontend_port: 9451
scripts/dev.sh           API 9450 + Vite 9451
Run-Chakshu.sh docker    9450 only
docker-compose.yml       9450:9450
desktop/main.js prod     loads 9450
desktop/main.js dev      loads 9451
run_windows.ps1          9450 (dist) | 9451 (dev)
run_portable.ps1         9450
```
