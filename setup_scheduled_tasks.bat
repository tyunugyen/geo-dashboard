@echo off
:: ================================================================
:: setup_scheduled_tasks.bat
:: Run ONCE to register both weekly and monthly scheduled tasks
:: Requires Admin privileges (right-click → Run as administrator)
:: ================================================================
echo Setting up GEO Dashboard scheduled tasks...
echo.

:: Weekly — every Monday 9am (single model, fast)
schtasks /create /tn "GEO Weekly Benchmark" ^
  /tr "C:\Users\tyunguyen\geo-dashboard\geo_weekly_benchmark.bat" ^
  /sc weekly /d MON /st 09:00 /f ^
  /ru "%USERNAME%"
echo   [OK] Weekly benchmark: every Monday 9:00am

:: Monthly — 1st Monday of month 9:30am (all 3 models)
:: Note: Windows Task Scheduler doesn't have "1st Monday" natively
:: So we run it monthly on day 1 at 9:30am as a close approximation
schtasks /create /tn "GEO Monthly Benchmark" ^
  /tr "C:\Users\tyunguyen\geo-dashboard\geo_monthly_benchmark.bat" ^
  /sc monthly /d 1 /st 09:30 /f ^
  /ru "%USERNAME%"
echo   [OK] Monthly benchmark: 1st of each month 9:30am

echo.
echo ============================================================
echo   Tasks registered. Verify in Task Scheduler:
echo   Start > Task Scheduler > Task Scheduler Library
echo   Look for: "GEO Weekly Benchmark" and "GEO Monthly Benchmark"
echo ============================================================
echo.
echo IMPORTANT: Make sure CAAS_API_KEY is set as a system
echo environment variable (not just session):
echo   setx CAAS_API_KEY "sk-your-key-here"
echo   (then restart any open Command Prompt windows)
echo.
pause
