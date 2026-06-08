# Install Python 3.12 and Node.js LTS on Windows (via winget).
# Run from Install-Prerequisites.bat or:
#   powershell -ExecutionPolicy Bypass -File scripts\install_prerequisites.ps1
param(
    [switch]$SkipNode,
    [switch]$Yes
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Test-Cmd([string]$name) {
    $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

function Get-PythonVersion {
    try {
        $out = & python --version 2>&1
        return [string]$out
    } catch {
        return $null
    }
}

function Get-NodeVersion {
    try {
        $out = & node --version 2>&1
        return [string]$out
    } catch {
        return $null
    }
}

function Install-WingetPackage([string]$id, [string]$label) {
    $args = @(
        "install", $id,
        "--accept-package-agreements",
        "--accept-source-agreements",
        "--disable-interactivity"
    )
    if ($Yes) { $args += "--silent" }
    Write-Host "    winget $($args -join ' ')"
    & winget @args
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1978335189) {
        # -1978335189 = already installed (winget exit code)
        throw "winget failed for $label (exit $LASTEXITCODE)"
    }
}

Write-Host ""
Write-Host " Chakshu - install Python 3.12 + Node.js (Windows)" -ForegroundColor Green
Write-Host ""

if (-not (Test-Cmd winget)) {
    Write-Host "ERROR: winget is not available on this PC." -ForegroundColor Red
    Write-Host ""
    Write-Host "Fix one of:"
    Write-Host "  1. Open Microsoft Store -> install / update 'App Installer'"
    Write-Host "  2. Install manually - see docs\COPY-TO-WINDOWS.md"
    Write-Host ""
    exit 1
}

# --- Python 3.12 ---
Write-Step "Python 3.12"
$pyVer = Get-PythonVersion
if ($pyVer -match "Python 3\.12") {
    Write-Host "    Already installed: $pyVer" -ForegroundColor Green
} else {
    if ($pyVer) {
        Write-Host "    Found $pyVer - installing Python 3.12 alongside (winget)."
    }
    Install-WingetPackage "Python.Python.3.12" "Python 3.12"
    Write-Host "    Close this window and open a NEW terminal, then run: python --version"
}

# --- Node.js LTS ---
if ($SkipNode) {
    Write-Step "Node.js LTS (skipped - use -SkipNode only if frontend/dist is pre-built)"
} else {
    Write-Step "Node.js LTS"
    $nodeVer = Get-NodeVersion
    if ($nodeVer) {
        Write-Host "    Already installed: $nodeVer" -ForegroundColor Green
    } else {
        Install-WingetPackage "OpenJS.NodeJS.LTS" "Node.js LTS"
        Write-Host "    Close this window and open a NEW terminal, then run: node --version"
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Prerequisites install finished." -ForegroundColor Green
Write-Host ""
Write-Host " Next steps:"
Write-Host "   1. Close ALL Command Prompt / PowerShell windows (refresh PATH)"
Write-Host "   2. Double-click Setup-Chakshu.bat"
Write-Host "   3. Double-click Run-Chakshu.bat"
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
