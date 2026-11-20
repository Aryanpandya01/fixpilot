# FixPilot one-time setup on a customer PC: Python packages + .env (Gemini key, support desk URL, access token),
# then checks that the key, the token and the cloud support desk all work. Run it through INSTALL_FIXPILOT.bat.
# "Continue": native tools (python, pip) write warnings to stderr, which "Stop" would turn into a crash.
# Every step checks $LASTEXITCODE or uses -ErrorAction Stop instead.
$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)
$Cloud = "https://fixpilot-server-382332871298.asia-south1.run.app"
function Say([string]$t, [string]$c = "Cyan") { Write-Host $t -ForegroundColor $c }
function Fail([string]$t) { Say "`n$t" Red; exit 1 }

Say "== FixPilot setup ==`n"

# 1. Python 3.10+ (the "py" launcher first; "python" can be the Microsoft Store stub)
$check = "import sys; print(sys.version_info >= (3, 10))"
$pyExe = $null; $pyArgs = @()
if ((Get-Command py -ErrorAction SilentlyContinue) -and ((& py -3 -c $check 2>$null) -eq "True")) { $pyExe = "py"; $pyArgs = @("-3") }
elseif ((Get-Command python -ErrorAction SilentlyContinue) -and ((& python -c $check 2>$null) -eq "True")) { $pyExe = "python" }
if (-not $pyExe) { Fail "Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), then run INSTALL_FIXPILOT.bat again." }
Say "[1/4] Python found: $(& $pyExe @pyArgs --version)"

# 2. Private Python environment + packages
if (-not (Test-Path ".venv\Scripts\python.exe")) { & $pyExe @pyArgs -m venv .venv; if ($LASTEXITCODE) { Fail "Could not create .venv" } }
Say "[2/4] Installing packages (first time takes a few minutes)..."
& .venv\Scripts\python.exe -m pip install --disable-pip-version-check -q -r agent\requirements.txt
if ($LASTEXITCODE) { Fail "Package install failed. Check the internet connection and run INSTALL_FIXPILOT.bat again." }

# 3. .env: keep what is there, ask only for what is missing
$lines = @(); if (Test-Path ".env") { $lines = @(Get-Content ".env" -Encoding UTF8) }
function Get-Val($k) { foreach ($l in $lines) { if ($l -match "^\s*$k\s*=\s*(.*)$") { return $Matches[1].Trim() } }; return "" }
function Set-Val($k, $v) {
    $script:lines = @($script:lines | Where-Object { $_ -notmatch "^\s*$k\s*=" }) + "$k=$v"
}
$key = Get-Val "GEMINI_API_KEY"
if (-not $key) { $key = (Read-Host "Paste your Gemini API key (free at https://aistudio.google.com/apikey)").Trim(); Set-Val "GEMINI_API_KEY" $key }
$token = Get-Val "FIXPILOT_TOKEN"
if (-not $token) { $token = (Read-Host "Paste the FixPilot access token (ask the FixPilot team)").Trim(); Set-Val "FIXPILOT_TOKEN" $token }
$server = Get-Val "SERVER_URL"
if (-not $server -or $server -match "localhost|127\.0\.0\.1") { $server = $Cloud; Set-Val "SERVER_URL" $server }
[IO.File]::WriteAllLines((Join-Path (Get-Location) ".env"), [string[]]$lines, (New-Object Text.UTF8Encoding $false))
Say "[3/4] Settings saved in .env (support desk: $server)"

# 4. Checks: Gemini key, support desk, access token
Say "[4/4] Checking..."
$env:FP_KEY = $key
& .venv\Scripts\python.exe -c "import os; from google import genai; c = genai.Client(api_key=os.environ['FP_KEY']); next(iter(c.models.list())); print('ok')" 2>$null | Out-Null
$keyOk = ($LASTEXITCODE -eq 0); Remove-Item Env:FP_KEY
if ($keyOk) { Say "  Gemini key ........ OK" Green } else { Say "  Gemini key ........ NOT working (check it in .env)" Red }
try { Invoke-RestMethod "$server/health" -TimeoutSec 60 -ErrorAction Stop | Out-Null; Say "  Support desk ...... OK ($server)" Green } catch { Say "  Support desk ...... can't reach $server" Red }
try {
    $code = (Invoke-RestMethod -Method Post "$server/sessions" -ContentType "application/json" -Body '{"query":"FixPilot setup check (ignore)","vendor_id":"billigo"}' -TimeoutSec 60 -ErrorAction Stop).code
    $h = @{ "X-FixPilot-Token" = $token }
    Invoke-RestMethod -Method Post "$server/sessions/$code/accept" -Headers $h -ContentType "application/json" -Body "{}" -TimeoutSec 60 -ErrorAction Stop | Out-Null
    Invoke-RestMethod -Method Post "$server/sessions/$code/finish" -Headers $h -ContentType "application/json" -Body '{"status":"stopped","summary":"Setup check"}' -TimeoutSec 60 -ErrorAction Stop | Out-Null
    Say "  Access token ...... OK" Green
} catch { Say "  Access token ...... REJECTED by the support desk (check FIXPILOT_TOKEN in .env)" Red }

Say "`nDone. Start FixPilot with START_FIXPILOT.bat" Green
Say "Tips: set Windows display scaling to 100%, keep the app you need help with open on the left, and close terminal windows." Gray
