@echo off
title Chakshu Forensics
cd /d "%~dp0"
if exist "%~dp0aive-api.exe" goto portable
if exist "%~dp0dist-backend\aive-api.exe" goto portable
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run_windows.ps1"
if errorlevel 1 (
  echo.
  echo  If setup is missing, run Setup-Chakshu.bat first.
  echo  Or use Chakshu-Portable.zip ^(extract and run, no setup^).
  pause
)
exit /b 0

:portable
if exist "%~dp0run_portable.ps1" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_portable.ps1"
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run_portable.ps1"
)
if errorlevel 1 pause
