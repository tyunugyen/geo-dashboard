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

echo Running PRIMARY Claude models (Sonnet, Haiku, Opus - 210 prompts, ~10 min)...
python geo_benchmark_multi_model.py --model claude-sonnet-4-6
python geo_benchmark_multi_model.py --model claude-haiku-4-5-20251001
python geo_benchmark_multi_model.py --model claude-opus-4-8
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

echo.
echo ============================================================
echo   Done. Dashboard updated.
echo   Weekly pulse check complete (Claude only).
echo   For full 9-model run: use geo_monthly_benchmark.bat
echo   View dashboard: file:///C:/Users/tyunguyen/geo-dashboard/public/index.html
echo ============================================================
echo.
