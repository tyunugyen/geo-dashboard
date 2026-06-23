@echo off
:: ================================================================
:: GEO Weekly Quick Benchmark — runs every Monday
:: Single-model run (Claude only, fast) for weekly tracking
:: ================================================================
echo.
echo ============================================================
echo   GEO Weekly Benchmark (Claude only)
echo   %DATE% %TIME%
echo ============================================================
echo.

cd /d C:\Users\tyunguyen\geo-dashboard

echo Running Claude-only benchmark (70 prompts, ~3 min)...
python geo_benchmark_runner.py --quiet 2>nul || python geo_benchmark_runner.py
if errorlevel 1 (
    echo ERROR: Benchmark failed. Check CAAS_API_KEY and VPN.
    exit /b 1
)

echo Updating dashboard...
python update_dashboard.py
if errorlevel 1 (
    echo ERROR: Dashboard update failed.
    git pull --rebase origin main
    python update_dashboard.py
)

echo.
echo ============================================================
echo   Done. Dashboard updated.
echo   For full 3-model run: use geo_monthly_benchmark.bat
echo ============================================================
