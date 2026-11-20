@echo off
REM FixPilot one-time setup for a customer PC (installs packages, asks for the Gemini key and access token, checks them).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0app\setup.ps1"
echo.
pause
