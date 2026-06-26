# Test GitHub repository_dispatch webhook
$token = "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"
$repo = "tyunugyen/geo-dashboard"
$week = Get-Date -Format "yyyy-'W'ww"

# Create a test session.json content
$testSession = @{
    meta = @{
        run_type = "webhook-test"
        run_id = "TEST-$(Get-Date -Format 'yyyy-MM-dd-HHmmss')"
        last_updated = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        test = $true
    }
    test_data = "This is a webhook test from PowerShell"
} | ConvertTo-Json -Depth 10

# Prepare the payload
$payload = @{
    event_type = "update-session"
    client_payload = @{
        content = $testSession
        week = $week
    }
} | ConvertTo-Json -Depth 10

# Send the webhook
$headers = @{
    "Authorization" = "token $token"
    "Accept" = "application/vnd.github+json"
    "Content-Type" = "application/json"
}

$url = "https://api.github.com/repos/$repo/dispatches"

Write-Host "Sending webhook to $url..."
Write-Host "Week: $week"
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $payload
    Write-Host "[OK] Webhook sent successfully!"
    Write-Host "Check https://github.com/$repo/actions for the workflow run."
} catch {
    Write-Host "[ERROR] Error sending webhook:"
    Write-Host $_.Exception.Message
    if ($_.ErrorDetails.Message) {
        Write-Host $_.ErrorDetails.Message
    }
}
