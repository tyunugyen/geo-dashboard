@echo off
:: ================================================================
:: GEO Claude Upgrade Push — run after Claude weekly/monthly session
:: Fires the receive-session.yaml dispatch with the latest session.json
:: ================================================================

echo.
echo ============================================================
echo   GEO Claude Upgrade — GitHub Dispatch
echo   %DATE% %TIME%
echo ============================================================
echo.

cd /d C:\Users\tyunguyen\geo-dashboard

:: Read current run_id from session.json
for /f "tokens=2 delims=:," %%a in ('powershell -Command "(Get-Content public/data/session.json | ConvertFrom-Json).meta.run_id"') do set RUN_ID=%%~a
for /f %%a in ('powershell -Command "(Get-Date -UFormat %%V)"') do set WEEK=%%a

echo Pushing session.json to GitHub...
echo Run ID: %RUN_ID%

git add public/data/session.json
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "GEO Claude upgrade: %RUN_ID% | live intel layer"
    git push origin main
    echo.
    echo ✅ Pushed — Vercel auto-deploying in ~30 seconds
    echo Dashboard: https://geo-dashboard-pi-three.vercel.app/
) else (
    echo No changes to session.json — nothing to push
)
echo.
pause
