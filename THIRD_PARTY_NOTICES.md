# Third-Party Notices

Chakshu Forensics (AI-IVE) includes third-party open-source software. This file
lists **major dependencies** declared in `requirements*.txt`, `pyproject.toml`,
and `frontend/package.json`. Package names and SPDX-style license identifiers
only — no secrets or credentials.

> **Note:** Exact license text for each package is in that package's source
> distribution or on [pypi.org](https://pypi.org) / [npmjs.com](https://www.npmjs.com).
> Re-run this inventory when dependencies change. **Legal review** is recommended
> before commercial redistribution, especially for copyleft components.

---

## Python — core (`requirements-fast.txt` / `pyproject.toml`)

| Package | Typical license |
|---------|-----------------|
| numpy | BSD-3-Clause |
| opencv-python-headless | Apache-2.0 |
| Pillow | HPND (PIL License) |
| fastapi | MIT |
| uvicorn | BSD-3-Clause |
| python-multipart | Apache-2.0 |
| cryptography | Apache-2.0 OR BSD-3-Clause (dual) |
| pysrt | GPL-3.0-only |
| PyYAML | MIT |

## Python — minimal install (`requirements-minimal.txt`)

Same as core except **no OpenCV**; adds:

| Package | Typical license |
|---------|-----------------|
| imageio-ffmpeg | BSD-2-Clause |

## Python — optional extras

| File | Package | Typical license |
|------|---------|-----------------|
| `requirements-ai.txt` | onnxruntime | MIT |
| `requirements-video.txt` | imageio-ffmpeg | BSD-2-Clause |
| `requirements-reports.txt` | reportlab | BSD-3-Clause |
| `requirements-reports.txt` | python-docx | MIT |
| `pyproject.toml` `[ui-legacy]` | PyQt6 | GPL-3.0-only OR commercial (Qt) |
| `pyproject.toml` `[dev]` | pytest | MIT |
| `pyproject.toml` `[dev]` | black | MIT |

## Bundled / runtime tools (not pip packages)

| Component | Typical license | Notes |
|-----------|-----------------|-------|
| FFmpeg (via imageio-ffmpeg or system PATH) | LGPL-2.1-or-later / GPL (build-dependent) | Used for video decode/encode |
| Electron (desktop shell) | MIT | See `desktop/package.json` when building desktop app |

---

## JavaScript — frontend (`frontend/package.json`)

| Package | Typical license |
|---------|-----------------|
| react | MIT |
| react-dom | MIT |
| vite | MIT |
| @vitejs/plugin-react | MIT |

---

## Copyleft and compliance notes

- **pysrt (GPL-3.0)** — Subtitle parsing. Evaluate GPL compatibility with
  proprietary distribution; consider alternative libraries or separate process
  isolation if counsel requires it.
- **PyQt6 (legacy UI only)** — Optional; not used by the default React UI.
  GPL or commercial Qt license applies if enabled.
- **FFmpeg** — License depends on build flags. Document which FFmpeg binary is
  shipped (pip bundle vs system) in release notes.

---

## How this file was generated

Dependency names were taken from:

- `requirements.txt` → `requirements-fast.txt`
- `requirements-minimal.txt`, `requirements-ai.txt`, `requirements-video.txt`, `requirements-reports.txt`
- `pyproject.toml` `[project]` and `[project.optional-dependencies]`
- `frontend/package.json`

License identifiers reflect commonly published metadata for these packages as of
the versions pinned in those files. Verify against installed package metadata
before audit sign-off:

```bash
pip install pip-licenses
pip-licenses --format=markdown
cd frontend && npm ls --all  # then check each package on npm
```
