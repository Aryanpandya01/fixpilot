# FixPilot: deploy the session server + support dashboard to Google Cloud Run (Mumbai).
# Usage (from the repo root, after `gcloud auth login`):
#   powershell -ExecutionPolicy Bypass -File server\deploy_cloudrun.ps1 -Project <PROJECT_ID>
param(
    [Parameter(Mandatory = $true)][string]$Project,
    [string]$Region = "asia-south1",   # Mumbai: lowest latency for India
    [string]$Service = "fixpilot-server"
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

# Shared secret: reuse the one in .env, or create one. The FixPilot app sends it as X-FixPilot-Token.
$envFile = ".env"
$token = (Select-String -Path $envFile -Pattern '^FIXPILOT_TOKEN=(.+)$' -ErrorAction SilentlyContinue | Select-Object -First 1).Matches.Groups[1].Value
if (-not $token) {
    $token = -join ((48..57) + (97..122) | Get-Random -Count 24 | ForEach-Object { [char]$_ })
    Add-Content -Path $envFile -Value "FIXPILOT_TOKEN=$token" -Encoding utf8
    Write-Host "Created FIXPILOT_TOKEN and saved it to .env"
}
$version = Get-Date -Format "yyyyMMdd-HHmm"

gcloud config set project $Project
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# Sessions live in memory, so run exactly ONE instance (min 1 = no cold start, max 1 = every code is
# found on the same instance). A second instance would not know codes created on the first.
gcloud run deploy $Service --source . --region $Region --allow-unauthenticated `
    --min-instances 1 --max-instances 1 --memory 512Mi --cpu 1 `
    --set-env-vars "FIXPILOT_TOKEN=$token,FIXPILOT_VERSION=$version"

$url = gcloud run services describe $Service --region $Region --format "value(status.url)"
Write-Host ""
Write-Host "==============================================================" -ForegroundColor Green
Write-Host "  FixPilot support desk is LIVE: $url" -ForegroundColor Green
Write-Host "  Put this in .env on every FixPilot PC:  SERVER_URL=$url" -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Green
