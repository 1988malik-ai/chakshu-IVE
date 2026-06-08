# Start pre-built Chakshu (no Python, no Node, no setup).
param(
    [string]$AppDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"

function Find-PortableLayout([string]$root) {
    $layouts = @(
        @{ Exe = Join-Path $root "aive-api.exe"; Dist = Join-Path $root "frontend-dist" },
        @{ Exe = Join-Path $root "dist-backend\aive-api.exe"; Dist = Join-Path $root "dist-backend\frontend-dist" }
    )
    foreach ($l in $layouts) {
        if ((Test-Path $l.Exe) -and (Test-Path (Join-Path $l.Dist "index.html"))) {
            return $l
        }
    }
    return $null
}

$layout = Find-PortableLayout $AppDir
if (-not $layout) {
    Write-Host "Portable build not found in:" -ForegroundColor Red
    Write-Host "  $AppDir"
    Write-Host ""
    Write-Host "Expected: aive-api.exe + frontend-dist\  (or dist-backend\)"
    Write-Host "Download Chakshu-Portable.zip from GitHub Actions, or run Build-Portable.bat once."
    exit 1
}

$hostAddr = "127.0.0.1"
$port = 9450
$url = "http://${hostAddr}:${port}"

Write-Host ""
Write-Host "  Chakshu Forensics (portable)" -ForegroundColor Cyan
Write-Host "  Opening $url" -ForegroundColor Green
Write-Host "  Close this window to stop Chakshu." -ForegroundColor Gray
Write-Host ""

Start-Process $url
Set-Location (Split-Path $layout.Exe -Parent)
& $layout.Exe --host $hostAddr --port $port --frontend-dist $layout.Dist
