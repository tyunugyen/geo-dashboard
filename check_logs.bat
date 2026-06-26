@echo off
echo ============================================================
echo Checking GEO Dashboard Task Logs
echo ============================================================
echo.

cd /d C:\Users\tyunguyen\geo-dashboard\logs

if not exist "*.log" (
    echo No log files found.
    echo Logs directory: C:\Users\tyunguyen\geo-dashboard\logs
    pause
    exit /b 0
)

echo Recent log files:
echo.
dir /o-d /b *.log | findstr /i "weekly monthly fill" 2>nul

echo.
echo ============================================================
echo Latest Weekly Benchmark:
echo ============================================================
for /f "delims=" %%f in ('dir /b /o-d weekly_benchmark*.log 2^>nul') do (
    echo File: %%f
    type "%%f" | findstr /i "started completed status error"
    goto :next_weekly
)
echo No weekly benchmark logs found.
:next_weekly

echo.
echo ============================================================
echo Latest Monthly Benchmark:
echo ============================================================
for /f "delims=" %%f in ('dir /b /o-d monthly_benchmark*.log 2^>nul') do (
    echo File: %%f
    type "%%f" | findstr /i "started completed status error"
    goto :next_monthly
)
echo No monthly benchmark logs found.
:next_monthly

echo.
echo ============================================================
echo Latest Fill Session:
echo ============================================================
for /f "delims=" %%f in ('dir /b /o-d fill_session*.log 2^>nul') do (
    echo File: %%f
    type "%%f" | findstr /i "started completed status error"
    goto :next_fill
)
echo No fill session logs found.
:next_fill

echo.
echo To view full log, open:
echo   C:\Users\tyunguyen\geo-dashboard\logs
echo.
pause
