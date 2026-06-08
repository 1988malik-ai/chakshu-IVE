# Build native Windows app (Electron window — no browser).
# Output: release\Chakshu-Native-1.0.0.exe
param(
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

if (-not $SkipBuild) {
    & "$PSScriptRoot\build_windows.ps1"
}

$nativeExe = Get-ChildItem "$Root\desktop\dist\Chakshu-Native-*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $nativeExe) {
    throw "Missing desktop\dist\Chakshu-Native-*.exe — Electron portable build failed"
}

$releaseDir = Join-Path $Root "release"
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
$dest = Join-Path $releaseDir $nativeExe.Name
Copy-Item $nativeExe.FullName $dest -Force

Write-Host ""
Write-Host "=== Native Windows app ready ===" -ForegroundColor Green
Write-Host "  $dest"
Write-Host ""
Write-Host "Copy this ONE file to any Windows PC and double-click it."
Write-Host "Opens a native Chakshu window — no browser, no Python, no setup."
