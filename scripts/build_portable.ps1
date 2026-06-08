# Build extract-and-run portable folder (no Python/Node needed on target PCs).
# Output: release\Chakshu-Portable\  and  release\Chakshu-Portable.zip
param(
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

if (-not $SkipBuild) {
    & "$PSScriptRoot\build_windows.ps1" -ApiOnly
}

$srcBackend = Join-Path $Root "dist-backend"
$exe = Join-Path $srcBackend "aive-api.exe"
$dist = Join-Path $srcBackend "frontend-dist"
if (-not (Test-Path $exe)) { throw "Missing $exe - run build first" }
if (-not (Test-Path (Join-Path $dist "index.html"))) { throw "Missing frontend build in $dist" }

$outDir = Join-Path $Root "release\Chakshu-Portable"
if (Test-Path $outDir) { Remove-Item -Recurse -Force $outDir }
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Copy-Item $exe $outDir
Copy-Item -Recurse $dist (Join-Path $outDir "frontend-dist")

@'
@echo off
title Chakshu Forensics
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_portable.ps1" -AppDir "%~dp0"
if errorlevel 1 pause
'@ | Set-Content -Path (Join-Path $outDir "Run-Chakshu.bat") -Encoding ASCII

Copy-Item "$PSScriptRoot\run_portable.ps1" $outDir

$zipPath = Join-Path $Root "release\Chakshu-Portable.zip"
if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
Compress-Archive -Path $outDir -DestinationPath $zipPath -Force

Write-Host ""
Write-Host "=== Portable build ready ===" -ForegroundColor Green
Write-Host "  Folder: release\Chakshu-Portable\"
Write-Host "  Zip:    release\Chakshu-Portable.zip"
Write-Host ""
Write-Host "Copy the zip to any Windows PC, unzip, double-click Run-Chakshu.bat"
Write-Host "No Python, Node, or Setup-Chakshu needed."
