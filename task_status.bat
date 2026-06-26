@echo off
echo ============================================================
echo GEO Dashboard - Scheduled Task Status
echo ============================================================
echo.

schtasks /query /tn "GEO Weekly Benchmark" /fo LIST /v | findstr /i "TaskName State LastRunTime NextRunTime LastResult"
echo.
echo ----

schtasks /query /tn "GEO Fill Session (Weekly)" /fo LIST /v | findstr /i "TaskName State LastRunTime NextRunTime LastResult"
echo.
echo ----

schtasks /query /tn "GEO Monthly Benchmark" /fo LIST /v | findstr /i "TaskName State LastRunTime NextRunTime LastResult"
echo.
echo ----

schtasks /query /tn "GEO Fill Session (Monthly)" /fo LIST /v | findstr /i "TaskName State LastRunTime NextRunTime LastResult"
echo.

echo ============================================================
echo Last Result Codes:
echo   0x0      = Success
echo   0x1      = Task failed or not run yet
echo   0x41301  = Task is currently running
echo ============================================================
echo.

echo To check detailed logs: run check_logs.bat
echo To test manually: Start-ScheduledTask -TaskName "GEO Weekly Benchmark"
echo.
pause
