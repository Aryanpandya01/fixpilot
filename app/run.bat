@echo off
REM FixPilot launcher: starts the local panel server (minimized), opens the panel and docks it on the right edge.
cd /d "%~dp0\.."

set "PY_EXE=python"
if exist ".venv\Scripts\python.exe" set "PY_EXE=.venv\Scripts\python.exe"
if exist "C:\Python313\python.exe" if not exist ".venv\Scripts\python.exe" set "PY_EXE=C:\Python313\python.exe"

set "EDGE_EXE="
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" set "EDGE_EXE=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" set "EDGE_EXE=C:\Program Files\Microsoft\Edge\Application\msedge.exe"

start "FixPilot server" /min "%PY_EXE%" -m uvicorn app.server:app --host 127.0.0.1 --port 8000
timeout /t 3 /nobreak >nul

if defined EDGE_EXE (
    start "" "%EDGE_EXE%" --app=http://127.0.0.1:8000 --user-data-dir="%LOCALAPPDATA%\FixPilotPanel" --no-first-run --no-default-browser-check
) else (
    start http://127.0.0.1:8000
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dock.ps1"
