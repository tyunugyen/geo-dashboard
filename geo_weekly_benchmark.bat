@echo off
:: ================================================================
:: GEO Weekly Benchmark — every Monday (Claude only, ~3 min)
:: Auto-extracts latest geo-dashboard.zip from Downloads first
:: ================================================================

set PATH=%PATH%;C:\Python313;C:\Python313\Scripts;C:\Program Files\Git\bin;C:\Program Files\Git\cmd;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\Scripts

echo.
echo ============================================================
echo   GEO Weekly Benchmark (Claude only)
echo   %DATE% %TIME%
echo ============================================================
echo.

cd /d C:\Users\tyunguyen\geo-dashboard
if errorlevel 1 (
    echo ERROR: Could not find geo-dashboard folder.
    pause
    exit /b 1
)

if "%CAAS_API_KEY%"=="" (
    echo ERROR: CAAS_API_KEY is not set.
    echo Run: setx CAAS_API_KEY "sk-your-key-here"
    pause
    exit /b 1
)

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH.
    pause
    exit /b 1
)

echo Running PRIMARY Claude model (Haiku only - 70 prompts, ~3 min)...
python geo_benchmark_multi_model.py --model claude-haiku-4-5-20251001
if errorlevel 1 (
    echo ERROR: Benchmark failed. Check CAAS_API_KEY and VPN.
    pause
    exit /b 1
)

echo Updating dashboard data.json (old format)...
python update_dashboard.py
if errorlevel 1 (
    git pull --rebase origin main
    python update_dashboard.py
    if errorlevel 1 (
        echo WARNING: Dashboard update_dashboard.py failed. Continuing with session.json...
    )
)

echo Generating session.json (new dynamic dashboard)...
python generate_session_json.py --weekly
if errorlevel 1 (
    echo ERROR: session.json generation failed.
    pause
    exit /b 1
)

echo Committing and pushing to GitHub...
git add benchmarks/*.csv public/data/session.json public/data.json
git commit -m "GEO benchmark: W%date:~-4%-%date:~4,2% | Unaided SOV 0%% | Weekly pulse check"
git push origin main
if errorlevel 1 (
    echo WARNING: git push failed. Check network connection or authentication.
    pause
    goto :skip_deploy
)

echo.
echo ============================================================
echo   MANUAL STEP: Trigger PaaS Deploy
echo ============================================================
echo.
echo GitHub updated successfully!
echo.
echo To update the live dashboard:
echo   Option 1: Run trigger_paas_deploy.bat (opens PaaS UI)
echo   Option 2: Go to https://host.beta.godaddy.com/paas/projects/kz6jwep09q
echo             Click "Pull from GitHub"
echo.
echo Dashboard will update in 30-60 seconds after pulling.
echo.

:skip_deploy

echo.
echo ============================================================
echo   Done. Dashboard updated and pushed to GitHub.
echo   Weekly pulse check complete (Claude Haiku only).
echo   GitHub Action will now fill intelligence layer automatically.
echo   For full 5-model run: use geo_monthly_benchmark.bat
echo   Dashboard: https://kz6jwep09q.c24.airoapp.ai/
echo   Local view: file:///C:/Users/tyunguyen/geo-dashboard/public/index.html
echo ============================================================
echo.
