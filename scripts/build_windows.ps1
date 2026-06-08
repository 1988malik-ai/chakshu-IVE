# Build Chakshu Windows installer (one command)
# Output: desktop\dist\Chakshu-Setup-1.0.0.exe
param(
    [switch]$SkipInstall,
    [switch]$ApiOnly
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

function Require-Command($name, $hint) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        throw "$name not found. $hint"
    }
}

Write-Host "=== Chakshu Windows build ===" -ForegroundColor Cyan
Require-Command node "Install Node.js LTS from https://nodejs.org/"
if (-not (Get-Command python -ErrorAction SilentlyContinue) -and -not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python 3.12 not found. Install from https://www.python.org/downloads/"
}

if (-not $SkipInstall -and -not (Test-Path "$Root\.venv\Scripts\python.exe")) {
    Write-Host "=== 0. Python environment ==="
    & "$PSScriptRoot\install.ps1" -y
}

$pip = "$Root\.venv\Scripts\pip.exe"
$py = "$Root\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "Missing .venv - run .\scripts\install.ps1" }

Write-Host "=== 1. React frontend ==="
Set-Location "$Root\frontend"
if (-not (Test-Path node_modules)) { npm install }
npm run build
Set-Location $Root

Write-Host "=== 2. Python API (PyInstaller) ==="
& $pip install -q pyinstaller
& "$Root\.venv\Scripts\pyinstaller.exe" --noconfirm "$Root\scripts\aive-api.spec"

$backendDir = Join-Path $Root "dist-backend"
if (Test-Path $backendDir) { Remove-Item -Recurse -Force $backendDir }
New-Item -ItemType Directory -Force -Path $backendDir | Out-Null
Copy-Item "$Root\dist\aive-api.exe" $backendDir
Copy-Item -Recurse "$Root\frontend\dist" (Join-Path $backendDir "frontend-dist")

Write-Host "      Backend bundle: dist-backend\"
Write-Host "        aive-api.exe"
Write-Host "        frontend-dist\"

if ($ApiOnly) {
    Write-Host ""
    Write-Host "ApiOnly: skipped Electron. Test with:" -ForegroundColor Yellow
    Write-Host "  cd dist-backend"
    Write-Host "  .\aive-api.exe --frontend-dist .\frontend-dist"
    Write-Host "  Open http://127.0.0.1:9450"
    exit 0
}

Write-Host "=== 3. Electron installer (NSIS) ==="
Set-Location "$Root\desktop"
if (-not (Test-Path node_modules)) { npm install }
$env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
npm run build

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Green
Write-Host "Installer: desktop\dist\Chakshu-Setup-*.exe"
Write-Host "Copy that file to any Windows PC and run it - no Python/Node needed on target machine."
