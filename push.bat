@echo off
echo ============================================
echo Push Session to GitHub
echo ============================================
echo.
cd /d C:\Users\tyunguyen\geo-dashboard
powershell.exe -ExecutionPolicy Bypass -File push-session.ps1
echo.
echo ============================================
echo.
pause
