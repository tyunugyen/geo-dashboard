@echo off
echo ============================================================
echo Dashboard Fix Verification
echo ============================================================
echo.

echo [1/3] Checking local session.json...
python -c "import json; s=json.load(open('public/data/session.json')); print(f'  Timestamp: {s[\"meta\"][\"last_updated\"]}'); print(f'  Competitors: {len(s[\"competitors\"])}'); print(f'  Categories: {len(s[\"categories\"])}'); print(f'  Model SOV: {len(s[\"model_sov\"][\"primary\"])}')"
echo.

echo [2/3] Waiting for PaaS deployment...
timeout /t 5 /nobreak >nul
echo.

echo [3/3] Checking what PaaS has deployed...
curl -s https://kz6jwep09q.c24.airoapp.ai/data/session.json 2>nul | findstr "last_updated competitors" | head -n 2
if %errorLevel% EQU 0 (
    echo   [OK] PaaS responded
) else (
    echo   [WAIT] PaaS still deploying - wait 2 more minutes
)
echo.

echo ============================================================
echo Next Steps:
echo 1. Wait 5 minutes total for PaaS to redeploy
echo 2. Open: https://kz6jwep09q.c24.airoapp.ai/
echo 3. Hard refresh: Ctrl+Shift+R
echo 4. Check:
echo    - 8 category boxes visible (was missing)
echo    - 8 competitors shown (was 5)
echo    - "What we track" loads (was Loading...)
echo ============================================================
pause
