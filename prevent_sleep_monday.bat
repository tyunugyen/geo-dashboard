@echo off
:: Prevent PC from sleeping until 2pm on Mondays
:: Run this Sunday night or set as a scheduled task for Sunday 11pm

echo Configuring power settings for Monday automation...
echo.

:: Disable sleep when plugged in (AC power)
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 30

:: Disable hibernate
powercfg /change hibernate-timeout-ac 0

echo.
echo ============================================================
echo Power settings updated:
echo   - Sleep: DISABLED when plugged in
echo   - Hibernate: DISABLED
echo   - Monitor timeout: 30 minutes
echo.
echo Your Monday tasks (9am-12:30pm) will now run uninterrupted.
echo.
echo To restore power saving later, run:
echo   powercfg /change standby-timeout-ac 30
echo ============================================================
pause
