# GEO Dashboard Automation Setup

This document explains how to use the automated GitHub Actions workflows for the GEO Dashboard.

## Overview

The GEO Dashboard has two automation workflows:

1. **`geo-session.yml`** - Fills session.json with intelligence data (runs on self-hosted runner)
2. **`receive-session.yaml`** - Receives session.json updates via webhook (runs on GitHub-hosted runner)

## Architecture

```
GoCaaS Scheduled Task                    GitHub Repository
┌────────────────────┐                  ┌──────────────────────┐
│                    │                  │                      │
│  Generate          │   Push via       │  receive-session     │
│  session.json  ────┼─────────────────>│  workflow            │
│                    │   webhook        │                      │
└────────────────────┘                  └──────────┬───────────┘
                                                   │
                                                   │ Commits
                                                   v
                                        ┌──────────────────────┐
                                        │                      │
                                        │  public/data/        │
                                        │  session.json        │
                                        │                      │
                                        └──────────┬───────────┘
                                                   │
                                                   │ Triggers
                                                   v
                                        ┌──────────────────────┐
                                        │                      │
                                        │  geo-session         │
                                        │  workflow            │
                                        │  (self-hosted)       │
                                        │                      │
                                        └──────────────────────┘
```

## Setup Complete ✅

The following have been configured:

- ✅ Self-hosted GitHub Actions runner installed and running as a Windows service
- ✅ Workflows configured to use Windows PowerShell (`shell: powershell`)
- ✅ `CAAS_API_KEY` secret configured in GitHub repository settings
- ✅ Webhook receiver workflow tested and working
- ✅ GitHub Personal Access Token created for webhook authentication

## Testing the Workflows

### Test Workflow 1: Receive Session via Webhook

Use the `push-to-github.ps1` script to test the webhook:

```powershell
cd C:\Users\tyunguyen\geo-dashboard

# Test with current session.json
.\push-to-github.ps1

# Test with specific file and run type
.\push-to-github.ps1 -SessionFile "path\to\session.json" -RunType monthly
```

This will:
1. Read the session.json file
2. Send it to GitHub via webhook
3. Trigger the `receive-session.yaml` workflow
4. The workflow commits the file as "GoCaaS Intelligence Bot"

### Test Workflow 2: Full Intelligence Pipeline

After the session.json is committed, the `geo-session.yml` workflow automatically triggers and:

1. ✅ Verifies Python is installed
2. ✅ Installs dependencies (openai package)
3. 🔄 Generates session.json skeleton (if using weekly/monthly mode)
4. 🔄 Fills session.json via Claude API
5. 🔄 Validates the output
6. 🔄 Commits the completed session.json back to the repo

Check the workflow status at: https://github.com/tyunguyen/geo-dashboard/actions

## Integration with GoCaaS

### Option 1: Direct Webhook Call

At the end of your GoCaaS scheduled task, call the push script:

```powershell
# Your existing GoCaaS code that generates session.json
# ...

# Push to GitHub when done
& "C:\Users\tyunguyen\geo-dashboard\push-to-github.ps1" `
    -SessionFile "C:\path\to\generated\session.json" `
    -RunType "weekly"
```

### Option 2: Scheduled Task

Create a Windows Scheduled Task that runs the GoCaaS pipeline + push:

```powershell
# Create a wrapper script
$script = @"
# Run GoCaaS intelligence generation
cd C:\path\to\gocaas
python generate_intelligence.py --weekly

# Push to GitHub
cd C:\Users\tyunguyen\geo-dashboard
.\push-to-github.ps1 -RunType weekly
"@

$script | Out-File "C:\scheduled\run-geo-weekly.ps1"

# Create scheduled task (run weekly on Monday at 6 AM)
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 6am
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\scheduled\run-geo-weekly.ps1"
Register-ScheduledTask -TaskName "GEO Weekly Intelligence" -Trigger $trigger -Action $action
```

### Option 3: Manual Trigger

You can also manually trigger the workflow via GitHub's UI:

1. Go to https://github.com/tyunguyen/geo-dashboard/actions
2. Select "GEO Session — Fill Intelligence Layer"
3. Click "Run workflow"
4. Choose "weekly" or "monthly"

## Monitoring

### Check Runner Status

```powershell
# Check if runner service is running
Get-Service "actions.runner.*"

# View recent runner logs
Get-Content "C:\actions-runner\_diag\Runner_*.log" -Tail 50
```

### Check Workflow Runs

- GitHub Actions UI: https://github.com/tyunguyen/geo-dashboard/actions
- Filter by workflow: "GEO Session" or "Receive Session"
- Check logs for each step

### Check Commits

```powershell
cd C:\Users\tyunguyen\geo-dashboard
git log --oneline -10
```

Look for commits from:
- "GoCaaS Intelligence Bot" (webhook receiver)
- "GEO Bot" (geo-session workflow)

## Troubleshooting

### Runner Not Picking Up Jobs

```powershell
# Restart the runner service
Restart-Service "actions.runner.tyunugyen-geo-dashboard.local-windows-runner"

# Check service status
Get-Service "actions.runner.*" | Format-List
```

### Workflow Failing at "Verify Python"

```powershell
# Test Python in runner work directory
cd C:\actions-runner\_work\geo-dashboard\geo-dashboard
py --version
py -m pip --version
```

### Webhook Not Triggering

```powershell
# Test webhook manually
cd C:\Users\tyunguyen\geo-dashboard
.\test-webhook.ps1

# Check if commit was created
git fetch origin
git log origin/main -1
```

### Missing API Key

If workflows fail with "CAAS_API_KEY not found":

1. Go to https://github.com/tyunguyen/geo-dashboard/settings/secrets/actions
2. Verify `CAAS_API_KEY` is listed
3. If missing, add it with your Claude API key

## Files Reference

- `.github/workflows/geo-session.yml` - Main intelligence workflow (self-hosted)
- `.github/workflows/receive-session.yaml` - Webhook receiver (GitHub-hosted)
- `.github/workflows/test-runner.yml` - Test workflow for debugging
- `push-to-github.ps1` - Production script for pushing session.json
- `test-webhook.ps1` - Test script for webhook debugging
- `generate_session_json.py` - Generates session.json skeleton
- `fill_session.py` - Fills session.json with Claude API

## Security Notes

⚠️ The GitHub PAT token has full `repo` access. Keep it secure:
- Token is stored in `push-to-github.ps1` - do not commit to public repos
- Token is also saved in memory file: `C:\Users\tyunguyen\.claude\projects\C--Users-tyunguyen\memory\reference_github_pat.md`
- To rotate: Generate new PAT in GitHub settings and update scripts

## Next Steps

1. ✅ Test full workflow (Step 2) - Verify the geo-session workflow works end-to-end
2. ✅ Test webhook (Step 3) - Verify push-to-github.ps1 works
3. 🔄 Integrate with existing GoCaaS pipeline
4. 🔄 Set up scheduled task for weekly runs
5. 🔄 Monitor first production run

---

Last updated: 2026-06-26
