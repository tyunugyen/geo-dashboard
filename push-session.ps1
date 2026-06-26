# Quick push session.json to GitHub via webhook
# Usage: powershell -File push-session.ps1

$ErrorActionPreference = "Stop"

# GitHub config
$token = "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"
$repo = "tyunugyen/geo-dashboard"

# Read session.json
Write-Host "Reading session.json..." -ForegroundColor Cyan
$sessionContent = Get-Content "public\data\session.json" -Raw
$session = $sessionContent | ConvertFrom-Json
Write-Host "  Run ID: $($session.meta.run_id)" -ForegroundColor Gray
Write-Host "  Run Type: $($session.meta.run_type)" -ForegroundColor Gray

# Prepare payload
$week = $session.meta.run_id
if (-not $week) { $week = Get-Date -Format "yyyy-'W'ww" }

$payload = @{
    event_type = "update-session"
    client_payload = @{
        content = $sessionContent
        week = $week
    }
} | ConvertTo-Json -Depth 10 -Compress

# Send webhook
Write-Host "`nSending webhook..." -ForegroundColor Cyan
$headers = @{
    "Authorization" = "token $token"
    "Accept" = "application/vnd.github+json"
    "Content-Type" = "application/json"
}

$url = "https://api.github.com/repos/$repo/dispatches"

try {
    Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $payload | Out-Null
    Write-Host "[SUCCESS] Pushed to GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Check status: https://github.com/$repo/actions" -ForegroundColor Cyan
} catch {
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
