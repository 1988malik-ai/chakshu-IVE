# AI-IVE Windows 64-bit build
$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}
& .\.venv\Scripts\pip.exe install -r requirements.txt
& .\.venv\Scripts\pip.exe install pyinstaller
& .\.venv\Scripts\pyinstaller.exe --noconfirm `
    --name AI-IVE `
    --windowed `
    --add-data "config;config" `
    --add-data "resources;resources" `
    --paths "src" `
    src/aive/main.py

Write-Host "Build complete: dist\AI-IVE\AI-IVE.exe"
