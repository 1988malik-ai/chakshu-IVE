@echo off
title Chakshu — Build portable (extract and run)
cd /d "%~dp0"
echo.
echo  Builds Chakshu-Portable.zip — no setup needed on other PCs.
echo  Requires Python 3.12 + Node.js on THIS machine only (one time).
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build_portable.ps1" %*
if errorlevel 1 goto fail
echo.
pause
exit /b 0

:fail
echo.
echo  BUILD FAILED — see errors above.
pause
exit /b 1
