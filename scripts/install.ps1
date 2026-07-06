# Windows dev environment — mirrors scripts/install.sh
param(
    [switch]$y
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

function Find-PythonExe {
    $candidates = @()
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($minor in 12, 13, 11) {
            # py launcher needs -3.12 not -12 (otherwise: "Unknown option: -1")
            $candidates += @{ Cmd = "py"; Args = @("-3.$minor") }
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $candidates += @{ Cmd = "python"; Args = @() }
    }

    foreach ($c in $candidates) {
        try {
            $ver = & $c.Cmd @($c.Args + @("-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")) 2>$null
            if ($ver -match "^3\.(11|12|13)$") {
                return $c
            }
        } catch { }
    }
    return $null
}

$Py = Find-PythonExe
if (-not $Py) {
    Write-Host "ERROR: Need Python 3.11, 3.12, or 3.13." -ForegroundColor Red
    Write-Host "  Install from https://www.python.org/downloads/ (check 'Add to PATH')"
    exit 1
}

Write-Host "=== Chakshu Windows install ===" -ForegroundColor Cyan
Write-Host "Python: $($Py.Cmd) $($Py.Args -join ' ')"

$recreate = $false
if (Test-Path ".venv") {
    if ($y) { $recreate = $true }
    else { Write-Host "Using existing .venv (run install.ps1 -y to recreate)" }
}
if ($recreate -or -not (Test-Path ".venv")) {
    if (Test-Path ".venv") { Remove-Item -Recurse -Force .venv }
    & $Py.Cmd @($Py.Args + @("-m", "venv", ".venv"))
}

$pip = Join-Path $Root ".venv\Scripts\pip.exe"
$python = Join-Path $Root ".venv\Scripts\python.exe"

Write-Host "[1/6] Upgrading pip, setuptools, wheel..."
& $python -m pip install -q --upgrade pip setuptools wheel

$wheelDir = Join-Path $Root "packaging\wheels\win-py312"
$useCache = Test-Path $wheelDir
if ($useCache) {
    $wheelCount = (Get-ChildItem $wheelDir -File -ErrorAction SilentlyContinue).Count
    Write-Host "[2/6] Installing packages ($wheelCount cached wheels + PyPI for any missing)..."
    # Cached sdists (e.g. pysrt.tar.gz) need setuptools; never use --no-index
    & $pip install --prefer-binary --find-links $wheelDir --only-binary=pysrt pysrt==1.1.2
    if ($LASTEXITCODE -ne 0) { throw "pip install pysrt failed (exit $LASTEXITCODE)" }
    & $pip install --prefer-binary --find-links $wheelDir -r requirements-fast.txt
    if ($LASTEXITCODE -ne 0) { throw "pip install requirements-fast.txt failed (exit $LASTEXITCODE)" }
    & $pip install --prefer-binary --find-links $wheelDir -r requirements-video.txt
    if ($LASTEXITCODE -ne 0) { throw "pip install requirements-video.txt failed (exit $LASTEXITCODE)" }
} else {
    Write-Host "[2/6] Installing packages (download from PyPI)..."
    & $pip install -q --prefer-binary -r requirements-fast.txt
    if ($LASTEXITCODE -ne 0) { throw "pip install requirements-fast.txt failed (exit $LASTEXITCODE)" }
    & $pip install -q --prefer-binary -r requirements-video.txt
    if ($LASTEXITCODE -ne 0) { throw "pip install requirements-video.txt failed (exit $LASTEXITCODE)" }
}

Write-Host "[3/6] Installing Chakshu package..."
& $pip install -q -e . --no-deps

Write-Host "[4/6] Verifying OpenCV..."
& $python -c "import cv2; print('      OpenCV', cv2.__version__, 'OK')"

Write-Host "[5/6] Checking media deps..."
& $python scripts/check-media-deps.py

Write-Host "[6/6] Installing report export (PDF/DOCX)..."
if ($useCache) {
    & $pip install --prefer-binary --find-links $wheelDir -r requirements-reports.txt
} else {
    & $pip install -q -r requirements-reports.txt
}
if ($LASTEXITCODE -ne 0) { throw "pip install requirements-reports.txt failed (exit $LASTEXITCODE)" }

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  `$env:PYTHONPATH='src'"
Write-Host "  python -m aive.api.server"
Write-Host ""
if (Test-Path (Join-Path $Root "frontend\dist\index.html")) {
    Write-Host "  Double-click Run-Chakshu.bat  ->  http://127.0.0.1:9450 (pre-built UI)"
} else {
    Write-Host "  Double-click Run-Chakshu.bat  ->  http://localhost:9451 (dev UI; API on 9450)"
}
