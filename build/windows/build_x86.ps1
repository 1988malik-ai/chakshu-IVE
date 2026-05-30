# AI-IVE Windows 32-bit legacy build (requires 32-bit Python)
$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $Root

& pyinstaller.exe --noconfirm `
    --name AI-IVE-x86 `
    --windowed `
    --add-data "config;config" `
    --add-data "resources;resources" `
    --paths "src" `
    src/aive/main.py

Write-Host "Build complete: dist\AI-IVE-x86\AI-IVE-x86.exe"
