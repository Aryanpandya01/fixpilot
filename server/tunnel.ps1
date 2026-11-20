# FixPilot backup: public HTTPS link to the LOCAL session server through a Cloudflare quick tunnel.
# No account needed. Works only while this laptop is on and this window stays open.
# Usage: powershell -ExecutionPolicy Bypass -File server\tunnel.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host "cloudflared is not installed. Run:  winget install --id Cloudflare.cloudflared  then open a new terminal." -ForegroundColor Yellow
    exit 1
}
if (-not (Get-NetTCPConnection -LocalPort 9000 -State Listen -ErrorAction SilentlyContinue)) {
    $py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
    Start-Process -FilePath $py -ArgumentList "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "9000" -WindowStyle Minimized
    Start-Sleep -Seconds 3
}
Write-Host "Starting tunnel... the public link is the https://....trycloudflare.com line below." -ForegroundColor Cyan
cloudflared tunnel --url http://localhost:9000 2>&1 | ForEach-Object {
    $line = "$_"
    if ($line -match "https://[a-z0-9-]+\.trycloudflare\.com") {
        Write-Host ""; Write-Host "  PUBLIC LINK: $($Matches[0])" -ForegroundColor Green; Write-Host ""
    }
}
