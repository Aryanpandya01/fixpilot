param(
    [string]$BaseUrl = "http://localhost:9000",
    [switch]$Pause,
    [string]$Code = "",
    [ValidateSet("email", "team", "product")]
    [string]$Task = "email"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " FixPilot Session Server Test Flow (BilliGo)" -ForegroundColor Cyan
Write-Host " Base URL: $BaseUrl" -ForegroundColor Cyan
Write-Host " Task    : $Task" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. GET /health
Write-Host "`n[Step 1] Checking /health..." -ForegroundColor Yellow
$health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
Write-Host "Health check response: $($health | ConvertTo-Json -Compress)" -ForegroundColor Green

# 2. Session setup (create new or use -Code)
$sessionCode = $Code
if ([string]::IsNullOrWhiteSpace($sessionCode)) {
    Write-Host "`n[Step 2] Creating new session..." -ForegroundColor Yellow
    
    if ($Task -eq "email") {
        $queryText = "Configure custom private domain email (Hostinger SMTP: aryan@projectw.in) and send test mail to aryanpandya0505@gmail.com"
    } elseif ($Task -eq "team") {
        $queryText = "Customer wants to add team member: Rahul Sharma, email: rahul@projectw.in, role: Sales"
    } else {
        $queryText = "Customer wants to add a new product: Parle-G, Rs 10, GST 18%"
    }

    $createBody = @{
        query = $queryText
        vendor_id = "billigo"
    } | ConvertTo-Json

    $createResp = Invoke-RestMethod -Uri "$BaseUrl/sessions" -Method Post -Body $createBody -ContentType "application/json"
    $sessionCode = $createResp.code
    Write-Host "Created Session Code: $sessionCode" -ForegroundColor Green
    Write-Host "Query: $queryText" -ForegroundColor DarkGray
} else {
    Write-Host "`n[Step 2] Using existing session code: $sessionCode" -ForegroundColor Green
}

# 3. GET /sessions/{code}
Write-Host "`n[Step 3] Fetching session details for code $sessionCode..." -ForegroundColor Yellow
$sessionDetails = Invoke-RestMethod -Uri "$BaseUrl/sessions/$sessionCode" -Method Get
Write-Host "Vendor Name    : $($sessionDetails.vendor_name)" -ForegroundColor Green
Write-Host "Status         : $($sessionDetails.status)" -ForegroundColor Green
Write-Host "Query          : $($sessionDetails.query)" -ForegroundColor Green
Write-Host "KB Text Length : $($sessionDetails.kb_text.Length) characters" -ForegroundColor Green

# 4. POST /sessions/{code}/accept
Write-Host "`n[Step 4] Accepting session $sessionCode..." -ForegroundColor Yellow
$acceptResp = Invoke-RestMethod -Uri "$BaseUrl/sessions/$sessionCode/accept" -Method Post -ContentType "application/json"
Write-Host "Accept response: $($acceptResp | ConvertTo-Json -Compress)" -ForegroundColor Green

# 5. Define events based on task
if ($Task -eq "email") {
    $events = @(
        @{
            type = "intent"
            text = "Navigate to Settings -> Email (SMTP)"
            action = "click"
        },
        @{
            type = "intent"
            text = "Select Hostinger provider (smtp.hostinger.com:465, SSL/TLS)"
            action = "click"
        },
        @{
            type = "intent"
            text = "Enter mailbox credentials for aryan@projectw.in and sender details"
            action = "type"
        },
        @{
            type = "intent"
            text = "Click 'Test connection' - SMTP connection verified"
            action = "click"
        },
        @{
            type = "intent"
            text = "Save SMTP configuration"
            action = "click"
        },
        @{
            type = "intent"
            text = "Send test email to aryanpandya0505@gmail.com"
            action = "click"
        },
        @{
            type = "done"
            text = "Custom private domain email configured and verified with test mail"
        }
    )
    $finalSummary = "Configured Hostinger SMTP for aryan@projectw.in on port 465 SSL/TLS and successfully sent test email to aryanpandya0505@gmail.com."
} elseif ($Task -eq "team") {
    $events = @(
        @{
            type = "intent"
            text = "Navigate to Settings -> Team members"
            action = "click"
        },
        @{
            type = "intent"
            text = "Click 'Add member' button"
            action = "click"
        },
        @{
            type = "intent"
            text = "Enter email 'rahul@projectw.in' and name 'Rahul Sharma'"
            action = "type"
        },
        @{
            type = "intent"
            text = "Select role 'Sales' from dropdown"
            action = "select"
        },
        @{
            type = "intent"
            text = "Click 'Add member' to submit invitation"
            action = "click"
        },
        @{
            type = "done"
            text = "Team member Rahul Sharma (Sales) added successfully"
        }
    )
    $finalSummary = "Successfully invited Rahul Sharma (rahul@projectw.in) as Sales to Shiv Enterprise."
} else {
    $events = @(
        @{
            type = "intent"
            text = "Click 'Products & services' in the left menu"
            action = "click"
        },
        @{
            type = "intent"
            text = "Type product name Parle-G 100g, Price Rs 10, GST 18%"
            action = "type"
        },
        @{
            type = "done"
            text = "Product Parle-G added with 18% GST"
        }
    )
    $finalSummary = "Added Parle-G at Rs 10 with 18% GST."
}

# 6. Stream events
Write-Host "`n[Step 5] Posting events..." -ForegroundColor Yellow
foreach ($ev in $events) {
    if ($Pause) {
        Write-Host "Pausing 2 seconds..." -ForegroundColor DarkGray
        Start-Sleep -Seconds 2
    }
    $evBody = $ev | ConvertTo-Json
    $evResp = Invoke-RestMethod -Uri "$BaseUrl/sessions/$sessionCode/events" -Method Post -Body $evBody -ContentType "application/json"
    Write-Host "Posted event [$($ev.type)]: $($ev.text)" -ForegroundColor Green
}

if ($Pause) {
    Write-Host "Pausing 2 seconds..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 2
}

# 7. POST /sessions/{code}/finish
Write-Host "`n[Step 6] Finishing session as solved..." -ForegroundColor Yellow
$finishBody = @{
    status = "solved"
    summary = $finalSummary
} | ConvertTo-Json

$finishResp = Invoke-RestMethod -Uri "$BaseUrl/sessions/$sessionCode/finish" -Method Post -Body $finishBody -ContentType "application/json"
Write-Host "Finish response: $($finishResp | ConvertTo-Json -Compress)" -ForegroundColor Green

# 8. GET /sessions/{code}/events
Write-Host "`n[Step 7] Getting session events summary..." -ForegroundColor Yellow
$eventsResp = Invoke-RestMethod -Uri "$BaseUrl/sessions/$sessionCode/events" -Method Get
$duration = [math]::Round($eventsResp.finished_at - $eventsResp.accepted_at, 2)
Write-Host "Final Status   : $($eventsResp.status)" -ForegroundColor Green
Write-Host "Summary        : $($eventsResp.summary)" -ForegroundColor Green
Write-Host "Event Count    : $($eventsResp.events.Count)" -ForegroundColor Green
Write-Host "Duration       : ${duration}s" -ForegroundColor Green

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host " Test Flow Completed Successfully!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
