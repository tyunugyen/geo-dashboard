# Setup GEO Dashboard Scheduled Tasks
# Run as Administrator

$ErrorActionPreference = "Stop"

Write-Host "=== Setting Up GEO Dashboard Scheduled Tasks ===" -ForegroundColor Cyan
Write-Host ""

# Check for existing tasks
$existingTasks = Get-ScheduledTask | Where-Object { $_.TaskName -like "GEO*" }
if ($existingTasks) {
    Write-Host "âš ï¸  Found existing GEO tasks:" -ForegroundColor Yellow
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
Write-Host "  âœ“ Created" -ForegroundColor Green

# Task 2: Weekly Fill (Every Monday at 10:00 AM - 1 hour after benchmark)
Write-Host "Creating: GEO Fill Session (Weekly)..." -ForegroundColor Yellow
$action2 = New-ScheduledTaskAction -Execute "$workingDir\geo_fill_session.bat" -WorkingDirectory $workingDir
$trigger2 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 10:00AM
Register-ScheduledTask -TaskName "GEO Fill Session (Weekly)" `
    -Description "Fill session.json with Claude intelligence after weekly benchmark" `
    -Action $action2 -Trigger $trigger2 -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "  âœ“ Created" -ForegroundColor Green

# Task 3: Monthly Benchmark (First Monday of month at 11:00 AM)
Write-Host "Creating: GEO Monthly Benchmark..." -ForegroundColor Yellow
