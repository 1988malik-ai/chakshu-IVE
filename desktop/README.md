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

## GitHub Actions + S3 publishing

The workflow `.github/workflows/build-windows.yml` builds on every push to `main`/`master` and publishes release artifacts to S3:

```text
s3://<CHAKSHU_S3_BUCKET>/chakshu/<branch>/<commit-sha>/
s3://<CHAKSHU_S3_BUCKET>/chakshu/latest/
```

Configure these repository secrets:

| Name | Purpose |
|------|---------|
| `CHAKSHU_S3_BUCKET` | Target bucket name, without `s3://` |
| `AWS_ACCESS_KEY_ID` | IAM access key with write access to the bucket |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |

Optional repository variable:

| Name | Default | Purpose |
|------|---------|---------|
| `AWS_REGION` | `ap-south-1` | Region used by `aws-actions/configure-aws-credentials` |

Artifacts uploaded:

- `Chakshu-Setup-*.exe` — NSIS installer
- `Chakshu-Native-*.exe` — native portable Electron app
- `Chakshu-Portable.zip` — browser/portable package
- `manifest.json` — file sizes, SHA-256 hashes, branch, commit, and workflow run metadata

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
