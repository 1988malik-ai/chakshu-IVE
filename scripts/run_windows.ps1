# Start Chakshu on Windows — double-click via Run-Chakshu.bat
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

if (-not (Test-Path "$Root\.venv\Scripts\python.exe")) {
    Write-Host "First-time setup..." -ForegroundColor Yellow
    & "$Root\scripts\install.ps1" -y
}

$frontend = Join-Path $Root "frontend"
$dist = Join-Path $frontend "dist"
$usePrebuiltUi = Test-Path (Join-Path $dist "index.html")

try {
    $old = Get-NetTCPConnection -LocalPort 9450 -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($old) {
        Write-Host "Note: port 9450 may already be in use." -ForegroundColor Yellow
    }
} catch { }

Write-Host ""
Write-Host "  Starting Chakshu..." -ForegroundColor Cyan

if ($usePrebuiltUi) {
    Write-Host "  Mode: pre-built UI (no npm needed)" -ForegroundColor Gray
    Write-Host "  Open: http://127.0.0.1:9450" -ForegroundColor Green
    Write-Host ""
    $env:PYTHONPATH = "src"
    $env:AIVE_FRONTEND_DIST = $dist
    Start-Process "http://127.0.0.1:9450"
    & "$Root\.venv\Scripts\python.exe" -m aive.api._launcher --host 127.0.0.1 --port 9450 --frontend-dist $dist
} else {
    if (-not (Test-Path "$frontend\node_modules")) {
        Write-Host "Installing UI (npm)..." -ForegroundColor Yellow
        Set-Location $frontend
        npm install
        Set-Location $Root
    }
    Write-Host "  Mode: dev UI" -ForegroundColor Gray
    Write-Host "  API:  http://127.0.0.1:9450" -ForegroundColor Green
    Write-Host "  UI:   http://localhost:9451" -ForegroundColor Green
    Write-Host "  Close this window to stop." -ForegroundColor Gray
    Write-Host ""

    $apiCmd = @"
Set-Location '$Root'
`$env:PYTHONPATH = 'src'
& '$Root\.venv\Scripts\python.exe' -m aive.api.server
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCmd -WindowStyle Minimized
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:9451"
    Set-Location $frontend
    npm run dev
}
