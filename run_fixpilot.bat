@echo off
REM FixPilot — All-in-One Real Product Launcher
REM Starts Session Server (9000), Local App Server (8000), opens Support Desk and docked Customer Panel.
cd /d "%~dp0"

echo ===================================================
echo  Starting FixPilot — Real Autonomous Support Suite
echo ===================================================

set "PY_EXE=python"
if exist ".venv\Scripts\python.exe" set "PY_EXE=.venv\Scripts\python.exe"
if exist "C:\Python313\python.exe" if not exist ".venv\Scripts\python.exe" set "PY_EXE=C:\Python313\python.exe"

set "EDGE_EXE="
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" set "EDGE_EXE=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" set "EDGE_EXE=C:\Program Files\Microsoft\Edge\Application\msedge.exe"

echo [1/4] Launching Session Server on http://localhost:9000 ...
start "FixPilot Session Server" /min "%PY_EXE%" -m uvicorn server.main:app --host 0.0.0.0 --port 9000

echo [2/4] Launching Desktop App Server on http://127.0.0.1:8000 ...
start "FixPilot Desktop Server" /min "%PY_EXE%" -m uvicorn app.server:app --host 127.0.0.1 --port 8000

timeout /t 3 /nobreak >nul

echo [3/4] Opening Support Desk in browser...
start http://localhost:9000

echo [4/4] Opening ^& Docking Customer Panel...
if defined EDGE_EXE (
    start "" "%EDGE_EXE%" --app=http://127.0.0.1:8000 --user-data-dir="%LOCALAPPDATA%\FixPilotPanel" --no-first-run --no-default-browser-check
) else (
    start http://127.0.0.1:8000
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0app\dock.ps1"

echo ===================================================
echo  FixPilot is now LIVE!
echo  - Support Desk: http://localhost:9000
echo  - Customer Panel: docked on the right
echo ===================================================
