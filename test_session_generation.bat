@echo off
:: Quick test of session.json generation
echo ============================================================
echo   Testing session.json generation
echo ============================================================
echo.

cd /d C:\Users\tyunguyen\geo-dashboard

echo Testing WEEKLY generation...
python generate_session_json.py --weekly
if errorlevel 1 (
    echo ERROR: Weekly generation failed
    pause
    exit /b 1
)
echo ✓ Weekly session.json generated
echo.

echo Opening dashboard in browser...
start "" "file:///C:/Users/tyunguyen/geo-dashboard/public/index.html"

echo.
echo ============================================================
echo   Test complete! Check the dashboard in your browser.
echo   - Header should show "Weekly pulse"
echo   - Last updated bar should show current timestamp
echo   - Should show "Last full benchmark: June 2026"
echo ============================================================
echo.
pause
