@echo off
:: ================================================================
:: Trigger GoDaddy PaaS Deploy Manually
:: Run this after any git push to force dashboard update
:: ================================================================

echo.
echo ============================================================
echo   Triggering GoDaddy PaaS Deploy
echo ============================================================
echo.

echo Opening PaaS dashboard in browser...
echo Click "Pull from GitHub" button to update dashboard
echo.

start https://host.beta.godaddy.com/paas/projects/kz6jwep09q

echo.
echo Waiting 10 seconds for you to click the button...
timeout /t 10 /nobreak >nul

echo.
echo Dashboard should update in 30-60 seconds
echo Dashboard URL: https://kz6jwep09q.c24.airoapp.ai/
echo.
echo ============================================================
pause
