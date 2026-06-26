# GEO Dashboard Automation - Quick Start Guide

## ✅ Setup Complete!

Your automation is ready to use. Here's how to use it:

---

## 📋 Step 2: Test Full Workflow

The full workflow test has been triggered (commit: 31eafd3). Check the status:

### 1. Open GitHub Actions
Go to: https://github.com/tyunguyen/geo-dashboard/actions

### 2. Look for "GEO Session — Fill Intelligence Layer"
You should see a workflow run with the commit message "Test full workflow with CAAS_API_KEY"

### 3. Click on the workflow run and check each step:
- ✅ **Checkout repo** - Should succeed
- ✅ **Verify Python** - Should succeed (we fixed the pwsh → powershell issue)
- ✅ **Install dependencies** - Should succeed (installs openai package)
- 🔄 **Generate session.json skeleton** - Check if this passes with your API key
- 🔄 **Fill session.json via Claude API** - Check if this completes
- 🔄 **Validate output** - Checks if session.json has required fields
- 🔄 **Commit completed session.json** - Commits back to repo

### 4. Expected Outcome:
If successful, you'll see a new commit from "GEO Bot" with message like:
```
[geo-bot] GEO session complete — 2026-06-W26-test
```

---

## 📋 Step 3: Integrate with GoCaaS

There are **3 ways** to integrate:

### Option A: Manual Push (Easiest for Testing)

```powershell
# Navigate to the repo
cd C:\Users\tyunguyen\geo-dashboard

# Push your session.json to GitHub
.\push-to-github.ps1

# Or specify a file location
.\push-to-github.ps1 -SessionFile "C:\path\to\session.json" -RunType weekly
```

**What happens:**
1. Script reads your session.json
2. Sends it to GitHub via webhook
3. GitHub commits it (you'll see "GoCaaS Intelligence Bot" commit)
4. This triggers the geo-session workflow automatically

---

### Option B: Add to Existing Script

If you already have a GoCaaS script that generates session.json, just add this at the end:

```powershell
# Your existing code...
# (code that generates session.json)

# Add this at the end:
Write-Host "Pushing to GitHub..."
& "C:\Users\tyunguyen\geo-dashboard\push-to-github.ps1" `
    -SessionFile ".\public\data\session.json" `
    -RunType "weekly"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully pushed to GitHub!"
} else {
    Write-Host "Failed to push to GitHub"
    exit 1
}
```

---

### Option C: Windows Scheduled Task

Create a scheduled task that runs your entire pipeline:

**Step 1: Create a wrapper script**

```powershell
# Save this as: C:\scheduled\run-geo-intelligence.ps1

# Set error handling
$ErrorActionPreference = "Stop"

# Log file
$logFile = "C:\scheduled\logs\geo-$(Get-Date -Format 'yyyy-MM-dd').log"
New-Item -ItemType Directory -Force -Path (Split-Path $logFile) | Out-Null

Start-Transcript -Path $logFile -Append

Write-Host "=========================================="
Write-Host "GEO Intelligence Run Started"
Write-Host "Time: $(Get-Date)"
Write-Host "=========================================="

try {
    # Step 1: Generate session.json (your existing GoCaaS code)
    Write-Host "`n[1/2] Generating intelligence data..."
    cd C:\Users\tyunguyen\geo-dashboard
    # REPLACE THIS with your actual intelligence generation command:
    # python generate_session_json.py --weekly
    # python fill_session.py
    
    # Step 2: Push to GitHub
    Write-Host "`n[2/2] Pushing to GitHub..."
    .\push-to-github.ps1 -RunType weekly
    
    if ($LASTEXITCODE -ne 0) {
        throw "Push to GitHub failed"
    }
    
    Write-Host "`n[SUCCESS] Intelligence run completed!" -ForegroundColor Green
    
} catch {
    Write-Host "`n[ERROR] Intelligence run failed: $_" -ForegroundColor Red
    exit 1
} finally {
    Stop-Transcript
}
```

**Step 2: Create the scheduled task**

Run this in PowerShell **as Administrator**:

```powershell
# Weekly run: Every Monday at 6:00 AM
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 6:00AM

# Or Monthly run: 1st of every month at 6:00 AM
# $trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At 6:00AM

$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-ExecutionPolicy Bypass -File C:\scheduled\run-geo-intelligence.ps1"

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName "GEO Weekly Intelligence" `
    -Description "Generate and push GEO intelligence data weekly" `
    -Trigger $trigger `
    -Action $action `
    -Settings $settings `
    -User $env:USERNAME `
    -RunLevel Highest

Write-Host "Scheduled task created successfully!"
Write-Host "Task Name: GEO Weekly Intelligence"
Write-Host "Schedule: Every Monday at 6:00 AM"
```

**Step 3: Test the scheduled task**

```powershell
# Run it manually to test
Start-ScheduledTask -TaskName "GEO Weekly Intelligence"

# Check the log
Get-Content "C:\scheduled\logs\geo-$(Get-Date -Format 'yyyy-MM-dd').log" -Tail 50
```

---

## 🔍 Monitoring

### Check if webhook worked:
```powershell
cd C:\Users\tyunguyen\geo-dashboard
git fetch origin
git log origin/main -5 --oneline --author="GoCaaS Intelligence Bot"
```

### Check if workflow ran:
Visit: https://github.com/tyunguyen/geo-dashboard/actions

### Check runner status:
```powershell
Get-Service "actions.runner.*"
```

---

## 🧪 Quick Test Right Now

Let's test the full cycle:

```powershell
# 1. Navigate to repo
cd C:\Users\tyunguyen\geo-dashboard

# 2. Push current session.json
.\push-to-github.ps1

# 3. Wait 10 seconds
Start-Sleep -Seconds 10

# 4. Check if commit appeared
git fetch origin
git log origin/main -1 --oneline

# 5. Check workflow status
Start-Process "https://github.com/tyunguyen/geo-dashboard/actions"
```

---

## ❓ Common Questions

**Q: How often does the workflow run?**
A: The workflow runs automatically whenever session.json is committed to the repo (either via webhook or direct push).

**Q: Can I run it manually?**
A: Yes! Go to GitHub Actions → "GEO Session — Fill Intelligence Layer" → "Run workflow" → Choose weekly/monthly.

**Q: How do I know if it worked?**
A: Check for a commit from "GEO Bot" with message "[geo-bot] GEO session complete — <run_id>"

**Q: What if it fails?**
A: Check the workflow logs on GitHub Actions page. Most common issues:
- CAAS_API_KEY not set → Add secret in repo settings
- Python packages missing → Runner will install automatically
- API rate limit → Wait and retry

**Q: Where are the logs?**
A: 
- GitHub Actions logs: https://github.com/tyunguyen/geo-dashboard/actions
- Runner logs: `C:\actions-runner\_diag\`
- Scheduled task logs: `C:\scheduled\logs\`

---

## 📝 Summary

**For testing/manual runs:**
```powershell
cd C:\Users\tyunguyen\geo-dashboard
.\push-to-github.ps1
```

**For automated runs:**
Set up the scheduled task (Option C above) and forget about it!

**To monitor:**
Visit https://github.com/tyunguyen/geo-dashboard/actions

---

✨ **You're all set!** The automation is ready to use.
