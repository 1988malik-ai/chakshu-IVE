@echo off
title Chakshu — One-time setup
cd /d "%~dp0"
echo.
echo  Chakshu one-time setup for Windows
echo  Needs: Python 3.12 + Node.js (install once from python.org and nodejs.org)
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install.ps1" -y
if errorlevel 1 goto fail
echo.
if exist frontend\dist\index.html (
  echo  Pre-built UI found — skipping npm install.
) else (
  echo  Installing UI ^(npm^)...
  cd frontend
  call npm install
  if errorlevel 1 goto fail
  cd ..
)
echo.
echo  ========================================
echo   Setup complete!
echo   Double-click Run-Chakshu.bat to start.
echo  ========================================
echo.
pause
exit /b 0

:fail
echo.
echo  SETUP FAILED — see errors above.
pause
exit /b 1
