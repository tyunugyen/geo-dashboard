@echo off
:: ================================================================
:: GEO Monthly Benchmark — runs 1st of each month
:: ================================================================
:: TROUBLESHOOTING: If this exits immediately:
:: 1. Make sure CAAS_API_KEY is set: run `setx CAAS_API_KEY "sk-..."` then restart
:: 2. Make sure you are on VPN
:: 3. Run manually first to confirm it works before scheduling

:: Set PATH to include Python and Git (needed when run from Task Scheduler)
set PATH=%PATH%;C:\Python313;C:\Python313\Scripts;C:\Program Files\Git\bin;C:\Program Files\Git\cmd;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\Scripts

echo.
echo ============================================================
echo   GEO Monthly Benchmark (All Models)
echo   %DATE% %TIME%
echo ============================================================
echo.

:: Navigate to repo
cd /d C:\Users\tyunguyen\geo-dashboard
if errorlevel 1 (
    echo ERROR: Could not find geo-dashboard folder.
    echo Expected: C:\Users\tyunguyen\geo-dashboard
    pause
    exit /b 1
)

:: Check API key
if "%CAAS_API_KEY%"=="" (
    echo ERROR: CAAS_API_KEY is not set.
    echo Run this in Command Prompt: setx CAAS_API_KEY "sk-your-key-here"
    echo Then close and reopen Command Prompt and try again.
    pause
    exit /b 1
)

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH.
    echo Make sure Python is installed and added to PATH.
    pause
    exit /b 1
)

echo Running benchmark: ALL models (Claude + GPT + Gemini + o3)...
echo This takes ~30-40 minutes. You can minimize this window.
python geo_benchmark_multi_model.py --models all --quiet
if errorlevel 1 (
    echo Retrying with core 3 models...
    python geo_benchmark_multi_model.py --models claude openai gemini --quiet
    if errorlevel 1 (
        echo ERROR: Benchmark failed. Check CAAS_API_KEY and VPN connection.
        pause
        exit /b 1
    )
)

echo Benchmark complete. Updating dashboard...
python update_dashboard.py
if errorlevel 1 (
    echo Dashboard push failed. Pulling latest from GitHub first...
    git pull --rebase origin main
    python update_dashboard.py
    if errorlevel 1 (
        echo ERROR: Dashboard update failed. Run manually: python update_dashboard.py
        pause
        exit /b 1
    )
)

echo.
echo ============================================================
echo   DONE.
echo   Dashboard: https://host.beta.godaddy.com/paas/projects/kz6jwep09q
echo   Next: open Claude and say "Run monthly GEO session."
echo ============================================================
echo.
