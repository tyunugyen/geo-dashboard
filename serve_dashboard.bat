@echo off
:: Serve dashboard locally with Python HTTP server (no CORS issues)
echo.
echo ============================================================
echo   Starting GEO Dashboard Local Server
echo ============================================================
echo.

cd /d C:\Users\tyunguyen\geo-dashboard\public

echo Dashboard will open at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server when done.
echo.

:: Open browser after 2 seconds
start "" timeout /t 2 /nobreak >nul && start http://localhost:8000

:: Start Python HTTP server
python -m http.server 8000
