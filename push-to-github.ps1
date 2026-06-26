<#
.SYNOPSIS
    Push session.json from GoCaaS to GitHub repo via webhook

.DESCRIPTION
    This script reads a session.json file and pushes it to the GitHub repository
    via repository_dispatch webhook, triggering the receive-session workflow.

.PARAMETER SessionFile
    Path to the session.json file to push (default: ./public/data/session.json)

.PARAMETER RunType
    Type of run: 'weekly' or 'monthly' (default: weekly)

.EXAMPLE
    .\push-to-github.ps1

.EXAMPLE
    .\push-to-github.ps1 -SessionFile "C:\path\to\session.json" -RunType monthly
#>

param(
    [string]$SessionFile = ".\public\data\session.json",
    [ValidateSet("weekly", "monthly")]
    [string]$RunType = "weekly"
)

# Configuration
$githubToken = "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"
$githubRepo = "tyunugyen/geo-dashboard"
$webhookUrl = "https://api.github.com/repos/$githubRepo/dispatches"

# Validate session file exists
if (-not (Test-Path $SessionFile)) {
    Write-Error "Session file not found: $SessionFile"
    exit 1
}

# Read session.json content
Write-Host "Reading session file: $SessionFile"
try {
    $sessionContent = Get-Content $SessionFile -Raw -Encoding UTF8
    $sessionJson = $sessionContent | ConvertFrom-Json

    # Validate it's valid JSON and has meta section
    if (-not $sessionJson.meta) {
        Write-Warning "Session file is missing 'meta' section, but continuing..."
    }

    Write-Host "  Run Type: $($sessionJson.meta.run_type)"
    Write-Host "  Run ID: $($sessionJson.meta.run_id)"
} catch {
    Write-Error "Failed to read or parse session file: $_"
    exit 1
}

# Determine week number for commit message
$week = Get-Date -Format "yyyy-'W'ww"
if ($sessionJson.meta.run_id) {
    $week = $sessionJson.meta.run_id
}

# Prepare webhook payload
$payload = @{
    event_type = "update-session"
    client_payload = @{
        content = $sessionContent
        week = $week
        run_type = $RunType
    }
} | ConvertTo-Json -Depth 10 -Compress

# Prepare headers
$headers = @{
    "Authorization" = "token $githubToken"
    "Accept" = "application/vnd.github+json"
    "Content-Type" = "application/json"
    "User-Agent" = "GoCaaS-Automation/1.0"
}

# Send webhook
Write-Host ""
Write-Host "Pushing to GitHub..."
Write-Host "  Repository: $githubRepo"
Write-Host "  Week: $week"
Write-Host "  Type: $RunType"
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri $webhookUrl -Method Post -Headers $headers -Body $payload -ErrorAction Stop

    Write-Host "[SUCCESS] Session pushed to GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "The session.json will be committed by the GitHub Action."
    Write-Host "Check the workflow status at:"
    Write-Host "  https://github.com/$githubRepo/actions" -ForegroundColor Cyan
    Write-Host ""

    exit 0
} catch {
    Write-Host "[ERROR] Failed to push to GitHub" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red

    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }

    exit 1
}
