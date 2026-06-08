@echo off
title Chakshu — Build native Windows app
cd /d "%~dp0"
echo.
echo  Builds Chakshu-Native-1.0.0.exe — native window, no browser.
echo  Requires Python 3.12 + Node.js on THIS machine only (one time).
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build_native.ps1" %*
if errorlevel 1 goto fail
echo.
pause
exit /b 0

:fail
echo.
echo  BUILD FAILED — see errors above.
pause
exit /b 1
