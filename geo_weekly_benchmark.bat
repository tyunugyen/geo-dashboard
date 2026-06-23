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

echo Running Claude benchmark (70 prompts, ~3 min)...
python geo_benchmark_runner.py
if errorlevel 1 (
    echo ERROR: Benchmark failed. Check CAAS_API_KEY and VPN.
    pause
    exit /b 1
)

echo Updating dashboard...
python update_dashboard.py
if errorlevel 1 (
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
echo   Done. Dashboard updated.
echo   For full 9-model run: use geo_monthly_benchmark.bat
echo ============================================================
echo.
