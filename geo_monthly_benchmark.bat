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

:: Auto-extract latest zip from Downloads if it exists
if exist "C:\Users\%USERNAME%\Downloads\geo-dashboard.zip" (
    echo Updating files from latest geo-dashboard.zip...
    powershell -Command "Expand-Archive -Path 'C:\Users\%USERNAME%\Downloads\geo-dashboard.zip' -DestinationPath 'C:\Users\tyunguyen\geo-dashboard' -Force"
    if errorlevel 1 (
        echo WARNING: Could not extract zip. Continuing with existing files.
    ) else (
        echo Files updated from zip.
        del "C:\Users\%USERNAME%\Downloads\geo-dashboard.zip"
        echo Zip deleted from Downloads.
    )
    echo.
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

echo Running benchmark: PRIMARY models (Claude Sonnet/Haiku/Opus + GPT-4o/5 + Gemini)...
echo This takes ~15-20 minutes. You can minimize this window.
python geo_benchmark_multi_model.py --model claude-sonnet-4-6 --quiet
python geo_benchmark_multi_model.py --model claude-haiku-4-5-20251001 --quiet
python geo_benchmark_multi_model.py --model claude-opus-4-8 --quiet
python geo_benchmark_multi_model.py --model gpt-4o --quiet
python geo_benchmark_multi_model.py --model gpt-5 --quiet
python geo_benchmark_multi_model.py --model gemini-2.5-pro --quiet
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

echo.
echo ============================================================
echo   DONE.
echo   Full 9-model monthly benchmark complete.
echo   Dashboard: https://host.beta.godaddy.com/paas/projects/kz6jwep09q
echo   Local view: file:///C:/Users/tyunguyen/geo-dashboard/public/index.html
echo   Next: open Claude and say "Run monthly GEO session."
echo ============================================================
echo.
