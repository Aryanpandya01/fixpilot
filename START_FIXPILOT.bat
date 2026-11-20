@echo off
REM Customer PC: start the FixPilot panel only. The support desk runs in the cloud (see SERVER_URL in .env).
cd /d "%~dp0"
if not exist ".env" (
    echo FixPilot is not set up yet. Double-click INSTALL_FIXPILOT.bat first.
    pause
    exit /b 1
)
call "%~dp0app\run.bat"
