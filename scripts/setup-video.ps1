# Windows — video support for AI-IVE
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "Run scripts\install.sh equivalent first (create .venv)"
    exit 1
}
.\.venv\Scripts\Activate.ps1
pip install -q -r requirements-video.txt
$env:PYTHONPATH = "src"
python scripts/check-media-deps.py
