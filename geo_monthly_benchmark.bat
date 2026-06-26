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

echo Running benchmark: PRIMARY models (Claude Sonnet/Haiku/Opus + GPT-4o + Gemini)...
echo This takes ~15-20 minutes. You can minimize this window.
python geo_benchmark_multi_model.py --model claude-sonnet-4-6
python geo_benchmark_multi_model.py --model claude-haiku-4-5-20251001
python geo_benchmark_multi_model.py --model claude-opus-4-8
python geo_benchmark_multi_model.py --model gpt-4o
python geo_benchmark_multi_model.py --model gemini-2.5-pro
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

echo Generating session.json (new dynamic dashboard)...
python generate_session_json.py --monthly
if errorlevel 1 (
    echo ERROR: session.json generation failed.
    pause
    exit /b 1
)

echo Committing and pushing to GitHub...
git add benchmarks/*.csv public/data/session.json public/data.json
git commit -m "GEO benchmark: %date:~-4%-%date:~4,2% | Full 5-model monthly benchmark"
git push origin main
if errorlevel 1 (
    echo WARNING: git push failed. Check network connection or authentication.
    pause
)

echo.
echo ============================================================
echo   DONE. Dashboard updated and pushed to GitHub.
echo   Full 5-model monthly benchmark complete.
echo   GitHub Action will now fill intelligence layer automatically.
echo   Dashboard: https://kz6jwep09q.c24.airoapp.ai/
echo   Local view: file:///C:/Users/tyunguyen/geo-dashboard/public/index.html
echo ============================================================
echo.
