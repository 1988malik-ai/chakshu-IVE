@echo off
title Chakshu Windows Build
cd /d "%~dp0"
echo.
echo  Building Chakshu Windows installer...
echo  Requires: Node.js + Python 3.12 (once on THIS machine only)
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build_windows.ps1" %*
if errorlevel 1 (
  echo.
  echo  BUILD FAILED — see errors above.
  pause
  exit /b 1
)
echo.
pause
