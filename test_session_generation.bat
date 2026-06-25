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

echo Starting local server...
echo Dashboard will open at: http://localhost:8000
echo.
start /B python -m http.server 8000 -d public >nul 2>&1

:: Wait 2 seconds for server to start
timeout /t 2 /nobreak >nul

echo Opening dashboard in browser...
start "" "http://localhost:8000"

echo.
echo ============================================================
echo   Test complete! Check the dashboard at http://localhost:8000
echo   - Header should show "Weekly pulse"
echo   - Last updated bar should show current timestamp
echo   - Should show "Last full benchmark: June 2026"
echo.
echo   Press Ctrl+C to stop the server when done, or just close
echo   this window.
echo ============================================================
echo.

:: Keep server running
python -m http.server 8000 -d public
