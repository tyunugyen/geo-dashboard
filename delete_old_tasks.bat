@echo off
echo Deleting old GEO Dashboard scheduled tasks...
echo.

REM Delete all tasks starting with "GEO"
schtasks /delete /tn "GEO Weekly Benchmark" /f 2>nul
if %errorLevel% EQU 0 (echo   [OK] Deleted: GEO Weekly Benchmark) else (echo   [SKIP] Not found: GEO Weekly Benchmark)

schtasks /delete /tn "GEO Monthly Benchmark" /f 2>nul
if %errorLevel% EQU 0 (echo   [OK] Deleted: GEO Monthly Benchmark) else (echo   [SKIP] Not found: GEO Monthly Benchmark)

schtasks /delete /tn "GEO Fill Session" /f 2>nul
if %errorLevel% EQU 0 (echo   [OK] Deleted: GEO Fill Session) else (echo   [SKIP] Not found: GEO Fill Session)

schtasks /delete /tn "GEO Fill Session (Weekly)" /f 2>nul
if %errorLevel% EQU 0 (echo   [OK] Deleted: GEO Fill Session (Weekly)) else (echo   [SKIP] Not found: GEO Fill Session (Weekly))

schtasks /delete /tn "GEO Fill Session (Monthly)" /f 2>nul
if %errorLevel% EQU 0 (echo   [OK] Deleted: GEO Fill Session (Monthly)) else (echo   [SKIP] Not found: GEO Fill Session (Monthly))

echo.
echo Done! Old tasks deleted.
echo Now run setup_scheduled_tasks.bat to create the new ones.
echo.
pause
