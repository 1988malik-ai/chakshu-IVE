# Start pre-built Chakshu (no Python, no Node, no setup).
# Compatible with Windows PowerShell 5.1+
$ErrorActionPreference = "Stop"

function Test-UiReady([string]$distDir) {
    return Test-Path (Join-Path $distDir "index.html")
}

function Find-PortableLayout([string]$root) {
    $layouts = @(
        @{ Exe = Join-Path $root "aive-api.exe"; Dist = Join-Path $root "frontend-dist" },
        @{ Exe = Join-Path $root "dist-backend\aive-api.exe"; Dist = Join-Path $root "dist-backend\frontend-dist" }
    )
    foreach ($l in $layouts) {
        if ((Test-Path $l.Exe) -and (Test-UiReady $l.Dist)) {
            return $l
        }
    }
    return $null
}

$AppDir = $PSScriptRoot
$layout = Find-PortableLayout $AppDir

# If zip was extracted with an extra nested folder, check parent once
if (-not $layout) {
    $parent = Split-Path $AppDir -Parent
    if ($parent) {
        $layout = Find-PortableLayout $parent
    }
}

if (-not $layout) {
    Write-Host "Portable build not found." -ForegroundColor Red
    Write-Host "  Looked in: $AppDir"
    if ($parent) { Write-Host "  And also: $parent" }
    Write-Host ""
    Write-Host "This folder must contain:"
    Write-Host "  aive-api.exe"
    Write-Host "  frontend-dist\index.html"
    Write-Host ""
    Write-Host "Tip: open the innermost Chakshu-Portable folder, then run Run-Chakshu.bat"
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
$exeDir = Split-Path $layout.Exe -Parent
Set-Location $exeDir
& $layout.Exe --host $hostAddr --port $port --frontend-dist "$($layout.Dist)"
