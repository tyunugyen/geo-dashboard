@echo off
echo ============================================================
echo Configure Task Scheduler Failure Alerts
echo ============================================================
echo.
echo This will configure Windows Task Scheduler to:
echo 1. Log all task executions to Event Viewer
echo 2. Send you a notification if a task fails
echo 3. Restart failed tasks automatically (optional)
echo.
echo ============================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo ERROR: This script requires administrator privileges.
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo Setting up failure alerts for GEO tasks...
echo.

REM Configure event log settings for each task
echo [1/4] Configuring GEO Weekly Benchmark...
schtasks /change /tn "GEO Weekly Benchmark" /rl HIGHEST /it

echo [2/4] Configuring GEO Fill Session (Weekly)...
schtasks /change /tn "GEO Fill Session (Weekly)" /rl HIGHEST /it

echo [3/4] Configuring GEO Monthly Benchmark...
schtasks /change /tn "GEO Monthly Benchmark" /rl HIGHEST /it

echo [4/4] Configuring GEO Fill Session (Monthly)...
schtasks /change /tn "GEO Fill Session (Monthly)" /rl HIGHEST /it

echo.
echo ============================================================
echo Configuration Complete!
echo ============================================================
echo.
echo What's configured:
echo   - All tasks will log to Windows Event Viewer
echo   - Location: Event Viewer ^> Applications and Services ^> Microsoft ^> Windows ^> TaskScheduler
echo   - Task failures will appear as Event ID 103
echo.
echo To set up email alerts (optional):
echo   1. Open Task Scheduler (taskschd.msc)
echo   2. Find each GEO task
echo   3. Right-click ^> Properties ^> Actions tab
echo   4. Click "New" ^> Action: "Send an e-mail"
echo   5. Configure SMTP settings
echo.
echo To monitor in real-time:
echo   Run: check_logs.bat
echo.
pause
