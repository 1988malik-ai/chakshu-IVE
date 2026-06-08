# Start pre-built Chakshu (no Python, no Node, no setup).
param(
    [string]$AppDir = ""
)

$ErrorActionPreference = "Stop"

function Resolve-AppDir([string]$dir) {
    if ([string]::IsNullOrWhiteSpace($dir)) {
        $dir = $PSScriptRoot
    } else {
        # Bat passes "%~dp0" which ends with \ and breaks PowerShell quoting (\" escapes the quote)
        $dir = $dir.Trim().Trim('"').TrimEnd('\', '/')
    }
    try {
        return (Resolve-Path -LiteralPath $dir).Path
    } catch {
        return $PSScriptRoot
    }
}

function Test-UiReady([string]$distDir) {
    $index = Join-Path $distDir "index.html"
    return (Test-Path -LiteralPath $index)
}

function Find-PortableLayout([string]$root) {
    $searchRoots = New-Object System.Collections.Generic.List[string]
    $searchRoots.Add($root) | Out-Null
    $cursor = $root
    for ($i = 0; $i -lt 3; $i++) {
        $parent = Split-Path -LiteralPath $cursor -Parent
        if (-not $parent -or $parent -eq $cursor) { break }
        $searchRoots.Add($parent) | Out-Null
        $cursor = $parent
    }

    foreach ($base in $searchRoots) {
        $layouts = @(
            @{ Exe = Join-Path $base "aive-api.exe"; Dist = Join-Path $base "frontend-dist" },
            @{ Exe = Join-Path $base "dist-backend\aive-api.exe"; Dist = Join-Path $base "dist-backend\frontend-dist" }
        )
        foreach ($l in $layouts) {
            if ((Test-Path -LiteralPath $l.Exe) -and (Test-UiReady $l.Dist)) {
                return $l
            }
        }
    }
    return $null
}

$AppDir = Resolve-AppDir $AppDir
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
Set-Location -LiteralPath (Split-Path -LiteralPath $layout.Exe -Parent)
& $layout.Exe --host $hostAddr --port $port --frontend-dist "$($layout.Dist)"
