# How to Run the Push Script

## Problem: Script Opens in Editor Instead of Running

When you type `.\push-to-github.ps1`, Windows opens it in an editor instead of executing it.

## Solution: Use These Commands Instead

### ✅ Method 1: Run with PowerShell explicitly (RECOMMENDED)

```cmd
cd C:\Users\tyunguyen\geo-dashboard
powershell -ExecutionPolicy Bypass -File push-session.ps1
```

### ✅ Method 2: One-liner from Command Prompt

Open **Command Prompt** (not PowerShell) and run:

```cmd
cd C:\Users\tyunguyen\geo-dashboard
powershell -ExecutionPolicy Bypass -File push-session.ps1
```

### ✅ Method 3: Create a BAT file (Easiest!)

I'll create a `push.bat` file you can double-click:

**File: `push.bat`**
```batch
@echo off
cd /d C:\Users\tyunguyen\geo-dashboard
powershell.exe -ExecutionPolicy Bypass -File push-session.ps1
pause
```

Then just **double-click `push.bat`** and it will run!

---

## Testing Right Now

Let's verify the webhook works. Run this command block:

```powershell
# Navigate to repo
cd C:\Users\tyunguyen\geo-dashboard

# Run the push script
powershell -ExecutionPolicy Bypass -File push-session.ps1

# Wait 5 seconds
Start-Sleep -Seconds 5

# Check if webhook created a commit
git fetch origin
git log origin/main -1 --oneline --author="GoCaaS"
```

You should see a commit from "GoCaaS Intelligence Bot" with the message like:
```
Weekly GEO session - W2026-06-W26-test - automated push
```

---

## If Nothing Happens

Try this debug version to see what's happening:

```powershell
cd C:\Users\tyunguyen\geo-dashboard

# Read session file
$session = Get-Content public\data\session.json -Raw | ConvertFrom-Json
Write-Host "Session run_id: $($session.meta.run_id)"

# Test webhook call
$token = "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"
$repo = "tyunugyen/geo-dashboard"
$payload = @{
    event_type = "update-session"
    client_payload = @{ 
        content = (Get-Content public\data\session.json -Raw)
        week = $session.meta.run_id 
    }
} | ConvertTo-Json -Depth 10

Write-Host "Sending to: https://api.github.com/repos/$repo/dispatches"
Invoke-RestMethod `
    -Uri "https://api.github.com/repos/$repo/dispatches" `
    -Method Post `
    -Headers @{
        "Authorization" = "token $token"
        "Accept" = "application/vnd.github+json"
        "Content-Type" = "application/json"
    } `
    -Body $payload

Write-Host "Done! Check: https://github.com/$repo/actions"
```

---

## What Should Happen

1. Script reads `public/data/session.json`
2. Sends it to GitHub via webhook
3. GitHub workflow "Receive Session from GoCaaS" runs
4. A new commit appears from "GoCaaS Intelligence Bot"
5. This triggers the "GEO Session" workflow automatically

Check status at: https://github.com/tyunguyen/geo-dashboard/actions
