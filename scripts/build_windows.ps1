# Build AI-IVE for Windows: React + Python API + Electron installer
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

Write-Host "=== 1. React frontend ==="
Set-Location "$Root\frontend"
npm install
npm run build
Set-Location $Root

Write-Host "=== 2. Python API (PyInstaller) ==="
& "$Root\.venv\Scripts\pip.exe" install pyinstaller
& "$Root\.venv\Scripts\pyinstaller.exe" --noconfirm --onefile `
  --name aive-api `
  --paths "$Root\src" `
  --collect-all cv2 `
  "$Root\src\aive\api\_launcher.py"

New-Item -ItemType Directory -Force -Path "$Root\dist-backend" | Out-Null
Copy-Item "$Root\dist\aive-api.exe" "$Root\dist-backend\"
Copy-Item -Recurse "$Root\frontend\dist" "$Root\dist-backend\frontend-dist"

Write-Host "=== 3. Electron installer ==="
Set-Location "$Root\desktop"
npm install
$env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
npm run build

Write-Host "Done. Check desktop\dist\"
