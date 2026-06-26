# Setup GEO Dashboard Scheduled Tasks
# Run as Administrator

$ErrorActionPreference = "Stop"

Write-Host "=== Setting Up GEO Dashboard Scheduled Tasks ===" -ForegroundColor Cyan
Write-Host ""

# Check for existing tasks
$existingTasks = Get-ScheduledTask | Where-Object { $_.TaskName -like "GEO*" }
if ($existingTasks) {
    Write-Host "⚠️  Found existing GEO tasks:" -ForegroundColor Yellow
    $existingTasks | ForEach-Object {
        Write-Host "  - $($_.TaskName) (Trigger: $($_.Triggers[0].StartBoundary))"
    }
    Write-Host ""
    $response = Read-Host "Overwrite existing tasks? (yes/no)"
    if ($response -ne "yes") {
        Write-Host "Cancelled. No changes made." -ForegroundColor Yellow
        exit
    }
    Write-Host ""
}

# Common settings
$workingDir = "C:\Users\tyunguyen\geo-dashboard"
$user = "$env:USERDOMAIN\$env:USERNAME"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable -AllowStartIfOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest

# Task 1: Weekly Benchmark (Every Monday at 9:00 AM)
Write-Host "Creating: GEO Weekly Benchmark..." -ForegroundColor Yellow
$action1 = New-ScheduledTaskAction -Execute "$workingDir\geo_weekly_benchmark.bat" -WorkingDirectory $workingDir
$trigger1 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9:00AM
Register-ScheduledTask -TaskName "GEO Weekly Benchmark" `
    -Description "Run GEO weekly benchmark (Claude only, ~12 min)" `
    -Action $action1 -Trigger $trigger1 -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "  ✓ Created" -ForegroundColor Green

# Task 2: Weekly Fill (Every Monday at 10:00 AM - 1 hour after benchmark)
Write-Host "Creating: GEO Fill Session (Weekly)..." -ForegroundColor Yellow
$action2 = New-ScheduledTaskAction -Execute "$workingDir\geo_fill_session.bat" -WorkingDirectory $workingDir
$trigger2 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 10:00AM
Register-ScheduledTask -TaskName "GEO Fill Session (Weekly)" `
    -Description "Fill session.json with Claude intelligence after weekly benchmark" `
    -Action $action2 -Trigger $trigger2 -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "  ✓ Created" -ForegroundColor Green

# Task 3: Monthly Benchmark (First Monday of month at 11:00 AM)
Write-Host "Creating: GEO Monthly Benchmark..." -ForegroundColor Yellow
$action3 = New-ScheduledTaskAction -Execute "$workingDir\geo_monthly_benchmark.bat" -WorkingDirectory $workingDir
# Note: PowerShell doesn't have "first Monday" trigger, so we use weekly and add condition
$trigger3 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 11:00AM
# Add condition to only run if it's the first Monday (day 1-7)
$trigger3Condition = '$day = (Get-Date).Day; if ($day -le 7) { exit 0 } else { exit 1 }'
$action3WithCondition = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"$trigger3Condition`" && `"$workingDir\geo_monthly_benchmark.bat`""
Register-ScheduledTask -TaskName "GEO Monthly Benchmark" `
    -Description "Run GEO monthly benchmark (9 models, ~20 min) - First Monday only" `
    -Action $action3 -Trigger $trigger3 -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "  ✓ Created (first Monday only)" -ForegroundColor Green

# Task 4: Monthly Fill (First Monday of month at 12:30 PM - 1.5 hours after benchmark)
Write-Host "Creating: GEO Fill Session (Monthly)..." -ForegroundColor Yellow
$action4 = New-ScheduledTaskAction -Execute "$workingDir\geo_fill_session.bat" -WorkingDirectory $workingDir
$trigger4 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 12:30PM
Register-ScheduledTask -TaskName "GEO Fill Session (Monthly)" `
    -Description "Fill session.json after monthly benchmark - First Monday only" `
    -Action $action4 -Trigger $trigger4 -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "  ✓ Created (first Monday only)" -ForegroundColor Green

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "✓ 4 tasks created successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Schedule:" -ForegroundColor Yellow
Write-Host "  Every Monday:"
Write-Host "    9:00 AM  - Weekly Benchmark (~12 min)"
Write-Host "    10:00 AM - Weekly Fill (~3 min) [1 hour gap]"
Write-Host ""
Write-Host "  First Monday of month:"
Write-Host "    11:00 AM - Monthly Benchmark (~20 min)"
Write-Host "    12:30 PM - Monthly Fill (~3 min) [1.5 hour gap]"
Write-Host ""
Write-Host "To test manually:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName 'GEO Fill Session (Weekly)'"
Write-Host ""
Write-Host "To view tasks:" -ForegroundColor Yellow
Write-Host '  Get-ScheduledTask | Where-Object {$_.TaskName -like "GEO*"}'
