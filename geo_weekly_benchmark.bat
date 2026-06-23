@echo off
:: ================================================================
:: GEO Weekly Quick Benchmark — every Monday
:: Claude Sonnet only (fast, ~3 min)
:: ================================================================
echo.
echo ============================================================
echo   GEO Weekly Benchmark (Claude only)
echo   %DATE% %TIME%
echo ============================================================
echo.
cd /d C:\Users\tyunguyen\geo-dashboard
python geo_benchmark_runner.py
if errorlevel 1 (
    echo ERROR: Benchmark failed. Check CAAS_API_KEY and VPN.
    exit /b 1
)
python update_dashboard.py
if errorlevel 1 (
    git pull --rebase origin main && python update_dashboard.py
)
echo.
echo ============================================================
echo   Done. Dashboard updated.
echo   For full multi-model run: use geo_monthly_benchmark.bat
echo ============================================================
