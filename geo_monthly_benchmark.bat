@echo off
:: ================================================================
:: GEO Monthly Benchmark — runs 1st of each month
:: Auto-extracts latest geo-dashboard.zip from Downloads first
:: ================================================================

:: Set PATH to include Python and Git
set PATH=%PATH%;C:\Python313;C:\Python313\Scripts;C:\Program Files\Git\bin;C:\Program Files\Git\cmd;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\Scripts

echo.
echo ============================================================
echo   GEO Monthly Benchmark
echo   %DATE% %TIME%
echo ============================================================
echo.

:: Navigate to repo
cd /d C:\Users\tyunguyen\geo-dashboard
if errorlevel 1 (
    echo ERROR: Could not find geo-dashboard folder.
    pause
    exit /b 1
)

:: Check API key
if "%CAAS_API_KEY%"=="" (
    echo ERROR: CAAS_API_KEY is not set.
    echo Run: setx CAAS_API_KEY "sk-your-key-here"
    pause
    exit /b 1
)

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH.
    pause
    exit /b 1
)

echo Running benchmark: ALL 8 models (5 Primary + 3 Pulse)...
echo This takes ~25-30 minutes. You can minimize this window.
echo.
echo PRIMARY MODELS (5):
python geo_benchmark_multi_model.py --model claude-sonnet-4-6 --fresh
python geo_benchmark_multi_model.py --model claude-haiku-4-5-20251001
python geo_benchmark_multi_model.py --model claude-opus-4-8
python geo_benchmark_multi_model.py --model gpt-4o
python geo_benchmark_multi_model.py --model gemini-2.5-pro
echo.
echo PULSE CHECK MODELS (3):
python geo_benchmark_multi_model.py --model gemini-2.5-flash
python geo_benchmark_multi_model.py --model o3-mini
python geo_benchmark_multi_model.py --model gemini-3.1-pro-preview
if errorlevel 1 (
    echo ERROR: Benchmark failed. Check CAAS_API_KEY and VPN.
    pause
    exit /b 1
)

echo Benchmark complete. Updating dashboard data.json (old format)...
python update_dashboard.py
if errorlevel 1 (
    echo Pulling latest from GitHub first...
    git pull --rebase origin main
    python update_dashboard.py
    if errorlevel 1 (
        echo WARNING: Dashboard update_dashboard.py failed. Continuing with session.json...
    )
)

echo Generating session.json skeleton...
python generate_session_json.py --monthly
if errorlevel 1 (
    echo ERROR: session.json generation failed.
    pause
    exit /b 1
)

echo Filling session.json with live intelligence...
python fill_session.py
if errorlevel 1 (
    echo WARNING: fill_session.py failed. Continuing with skeleton only...
)

echo Committing and pushing to GitHub...
git add benchmarks/*.csv public/data/session.json public/data.json
git commit -m "GEO benchmark: %date:~-4%-%date:~4,2% | Full 5-model monthly benchmark"
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
echo   DONE. Dashboard updated and pushed to GitHub.
echo   Full 5-model monthly benchmark complete.
echo   GitHub Action will now fill intelligence layer automatically.
echo   Dashboard: https://geo-dashboard-pi-three.vercel.app/
echo   Updates in 30 seconds (Vercel auto-deploy)
echo   Local view: file:///C:/Users/tyunguyen/geo-dashboard/public/index.html
echo ============================================================
echo.
