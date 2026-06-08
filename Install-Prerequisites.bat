@echo off
setlocal EnableDelayedExpansion
title Chakshu — Install Python 3.12 + Node.js
cd /d "%~dp0"

set SKIP_NODE=0
if /I "%~1"=="-SkipNode" set SKIP_NODE=1

echo.
echo  Installs Python 3.12 and Node.js LTS using winget.
echo  Needs: Windows 10/11 with App Installer (winget).
echo  Run as Administrator if the install asks for permission.
echo.
if "%SKIP_NODE%"=="1" (
  echo  Mode: Python only ^(-SkipNode^)
) else (
  echo  Skip Node.js only if frontend\dist is already in the zip:
  echo    Install-Prerequisites.bat -SkipNode
)
echo.

where winget >nul 2>&1
if errorlevel 1 (
  echo  ERROR: winget is not available on this PC.
  echo.
  echo  Fix: Microsoft Store -^> install or update "App Installer"
  echo  Or install manually:
  echo    Python 3.12: https://www.python.org/downloads/
  echo    Node.js LTS: https://nodejs.org/
  goto fail
)

echo  [1/2] Python 3.12...
python --version 2>nul | findstr /R /C:"3\.12" >nul
if not errorlevel 1 (
  echo    Already installed:
  python --version
) else (
  echo    Installing via winget...
  winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements --disable-interactivity
  if errorlevel 1 (
    echo    winget finished with a warning — often means already installed. Check: python --version
  )
)

if "%SKIP_NODE%"=="1" (
  echo.
  echo  [2/2] Node.js LTS — skipped
) else (
  echo.
  echo  [2/2] Node.js LTS...
  where node >nul 2>&1
  if not errorlevel 1 (
    echo    Already installed:
    node --version
  ) else (
    echo    Installing via winget...
    winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements --disable-interactivity
    if errorlevel 1 (
      echo    winget finished with a warning — often means already installed. Check: node --version
    )
  )
)

echo.
echo  ========================================
echo   Prerequisites install finished.
echo.
echo   Next:
echo   1. Close ALL Command Prompt windows ^(refresh PATH^)
echo   2. Double-click Setup-Chakshu.bat
echo   3. Double-click Run-Chakshu.bat
echo  ========================================
echo.
pause
exit /b 0

:fail
echo.
pause
exit /b 1
