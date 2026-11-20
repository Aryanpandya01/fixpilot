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

REM The Support Desk is wherever SERVER_URL in .env points (Cloud Run when deployed, else this laptop).
set "SERVER_URL=http://localhost:9000"
for /f "usebackq tokens=1,* delims==" %%a in (".env") do if /i "%%a"=="SERVER_URL" set "SERVER_URL=%%b"

echo %SERVER_URL% | "%SystemRoot%\System32\find.exe" /i "localhost" >nul
if errorlevel 1 (
    echo [1/4] Using the cloud Support Desk: %SERVER_URL%
) else (
    echo [1/4] Launching Session Server on http://localhost:9000 ...
    start "FixPilot Session Server" /min "%PY_EXE%" -m uvicorn server.main:app --host 0.0.0.0 --port 9000
)

echo [2/4] Launching Desktop App Server on http://127.0.0.1:8000 ...
start "FixPilot Desktop Server" /min "%PY_EXE%" -m uvicorn app.server:app --host 127.0.0.1 --port 8000

timeout /t 3 /nobreak >nul

echo [3/4] Opening Support Desk in browser...
start "" "%SERVER_URL%"

echo [4/4] Opening ^& Docking Customer Panel...
if defined EDGE_EXE (
    start "" "%EDGE_EXE%" --app=http://127.0.0.1:8000 --user-data-dir="%LOCALAPPDATA%\FixPilotPanel" --no-first-run --no-default-browser-check
) else (
    start http://127.0.0.1:8000
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0app\dock.ps1"

echo ===================================================
echo  FixPilot is now LIVE!
echo  - Support Desk: %SERVER_URL%
echo  - Customer Panel: docked on the right
echo ===================================================
