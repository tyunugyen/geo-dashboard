@echo off
:: ================================================================
:: GEO Monthly Benchmark — runs 1st of each month
:: Runs Claude + GPT-4o + Gemini via GoCode proxy
:: ================================================================

set PATH=%PATH%;C:\Python313;C:\Python313\Scripts;C:\Program Files\Git\bin;C:\Program Files\Git\cmd;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\Scripts

echo.
echo ============================================================
echo   GEO Monthly Benchmark (9 models: 6 primary + 3 pulse)
echo   %DATE% %TIME%
echo ============================================================
echo.

cd /d C:\Users\tyunguyen\geo-dashboard
if errorlevel 1 (
    echo ERROR: Could not find geo-dashboard folder.
    pause & exit /b 1
)

:: Auto-extract latest zip from Downloads if it exists
if exist "C:\Users\%USERNAME%\Downloads\geo-dashboard.zip" (
    echo Updating files from latest geo-dashboard.zip...
    powershell -Command "Expand-Archive -Path 'C:\Users\%USERNAME%\Downloads\geo-dashboard.zip' -DestinationPath 'C:\Users\tyunguyen\geo-dashboard' -Force"
    del "C:\Users\%USERNAME%\Downloads\geo-dashboard.zip" 2>nul
    echo Files updated.
    echo.
)

if "%CAAS_API_KEY%"=="" (
    echo ERROR: CAAS_API_KEY is not set.
    echo Run: setx CAAS_API_KEY "sk-your-key"
    pause & exit /b 1
)

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH.
    pause & exit /b 1
)

echo Running benchmark: Claude + GPT-4o + Gemini (9 models, ~15 min)...
echo.
python geo_benchmark_multi_model.py --models claude openai gemini
if errorlevel 1 (
    echo.
    echo Retrying with Claude only...
    python geo_benchmark_runner.py
    if errorlevel 1 (
        echo ERROR: Benchmark failed. Check CAAS_API_KEY and VPN.
        pause & exit /b 1
    )
)

echo Benchmark complete. Updating dashboard...
python update_dashboard.py
if errorlevel 1 (
    git pull --rebase origin main
    python update_dashboard.py
    if errorlevel 1 (
        echo ERROR: Dashboard update failed.
        pause & exit /b 1
    )
)

echo.
echo ============================================================
echo   DONE.
echo   Dashboard: https://host.beta.godaddy.com/paas/projects/kz6jwep09q
echo   Next: open Claude and say "Run monthly GEO session."
echo ============================================================
echo.
