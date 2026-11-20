param(
    [string]$Code = "",
    [string]$Server = "http://localhost:9000",
    [string]$Password = "",
    [ValidateSet("team", "email", "custom")]
    [string]$Task = "team",
    [string]$Query = "",
    [string]$AppUrl = "",
    [switch]$ClearFirst,
    [switch]$Headless,
    [double]$Delay = 1.5
)

$ErrorActionPreference = "Stop"

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host " FixPilot — Live BilliGo Autonomous Execution" -ForegroundColor Cyan
Write-Host " Task       : $Task" -ForegroundColor Cyan
Write-Host " Server     : $Server" -ForegroundColor Cyan
if (![string]::IsNullOrWhiteSpace($AppUrl)) {
    Write-Host " Target App : $AppUrl" -ForegroundColor Cyan
}
Write-Host "=================================================" -ForegroundColor Cyan

$sessionCode = $Code
if ([string]::IsNullOrWhiteSpace($sessionCode)) {
    Write-Host "`n[1/3] Generating new FixPilot session code..." -ForegroundColor Yellow

    if (![string]::IsNullOrWhiteSpace($Query)) {
        $queryText = $Query
    } elseif ($Task -eq "team") {
        $queryText = "Customer wants to add team member: Rahul Sharma, email: rahul@projectw.in, role: Sales"
    } else {
        $queryText = "Configure custom private domain email (Hostinger SMTP for aryan@projectw.in) and send test mail to aryanpandya0505@gmail.com"
    }

    $createBody = @{
        query = $queryText
        vendor_id = "billigo"
    } | ConvertTo-Json

    $createResp = Invoke-RestMethod -Uri "$Server/sessions" -Method Post -Body $createBody -ContentType "application/json"
    $sessionCode = $createResp.code
    Write-Host "Created Session Code : $sessionCode" -ForegroundColor Green
    Write-Host "Query Text           : $queryText" -ForegroundColor DarkGray
    Write-Host "Open your Support Dashboard at $Server to watch live!" -ForegroundColor Magenta
} else {
    Write-Host "`n[1/3] Using existing session code: $sessionCode" -ForegroundColor Green
}

Write-Host "`n[2/3] Launching Live Autonomous Browser Agent..." -ForegroundColor Yellow
Write-Host "Watch FixPilot navigate, fill forms, and stream events live to Support Desk!" -ForegroundColor DarkGray

$cmdArgs = @("server/live_agent.py", "--code", $sessionCode, "--server", $Server, "--delay", $Delay.ToString())

if (![string]::IsNullOrWhiteSpace($AppUrl)) {
    $cmdArgs += @("--app-url", $AppUrl)
}

if (![string]::IsNullOrWhiteSpace($Password)) {
    $cmdArgs += @("--password", $Password)
    Write-Host "[INFO] Mailbox password supplied via command line argument." -ForegroundColor Green
} else {
    Write-Host "[INFO] Password mode: Human-in-the-Loop secure entry (or parsed from query)." -ForegroundColor DarkGray
}

if ($ClearFirst) {
    $cmdArgs += "--clear-first"
}
if ($Headless) {
    $cmdArgs += "--headless"
}

python -u @cmdArgs
