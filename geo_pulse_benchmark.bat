@echo off
:: ================================================================
:: GEO Pulse Benchmark — runs reasoning/preview models only
:: Includes retry logic and longer timeouts for stability
:: ================================================================

:: Set PATH to include Python and Git
set PATH=%PATH%;C:\Python313;C:\Python313\Scripts;C:\Program Files\Git\bin;C:\Program Files\Git\cmd;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\Scripts

echo.
echo ============================================================
echo   GEO Pulse Benchmark - Reasoning Models Only
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

echo ============================================================
echo   PULSE Models: Reasoning + Preview (with retry logic)
echo   These models are SLOWER and may need 60-120s per prompt
echo   Total time: ~30-45 minutes for all 3 models
echo ============================================================
echo.

:: ─────────────────────────────────────────────────────────────
:: o3 - OpenAI Reasoning Model
:: ─────────────────────────────────────────────────────────────
echo [1/3] Running o3 (OpenAI reasoning model)...
echo       Timeout: 120s per prompt, Rate limit: 10s between prompts
python geo_benchmark_multi_model.py --model o3
if errorlevel 1 (
    echo WARNING: o3 benchmark had errors. Retrying once...
    timeout /t 10 /nobreak >nul
    python geo_benchmark_multi_model.py --model o3
    if errorlevel 1 (
        echo ERROR: o3 benchmark failed twice. Continuing with other models...
    ) else (
        echo SUCCESS: o3 completed on retry.
    )
) else (
    echo SUCCESS: o3 completed.
)
echo.

:: ─────────────────────────────────────────────────────────────
:: o3-mini - OpenAI Reasoning Model (smaller)
:: ─────────────────────────────────────────────────────────────
echo [2/3] Running o3-mini (OpenAI reasoning model - mini)...
echo       Timeout: 120s per prompt, Rate limit: 10s between prompts
python geo_benchmark_multi_model.py --model o3-mini
if errorlevel 1 (
    echo WARNING: o3-mini benchmark had errors. Retrying once...
    timeout /t 10 /nobreak >nul
    python geo_benchmark_multi_model.py --model o3-mini
    if errorlevel 1 (
        echo ERROR: o3-mini benchmark failed twice. Continuing...
    ) else (
        echo SUCCESS: o3-mini completed on retry.
    )
) else (
    echo SUCCESS: o3-mini completed.
)
echo.

:: ─────────────────────────────────────────────────────────────
:: Gemini 3.1 Pro Preview - Google Next-Gen
:: ─────────────────────────────────────────────────────────────
echo [3/3] Running gemini-3.1-pro-preview (Google next-gen)...
echo       Timeout: 120s per prompt, Rate limit: 10s between prompts
python geo_benchmark_multi_model.py --model gemini-3.1-pro-preview
if errorlevel 1 (
    echo WARNING: gemini-3.1-pro-preview benchmark had errors. Retrying once...
    timeout /t 10 /nobreak >nul
    python geo_benchmark_multi_model.py --model gemini-3.1-pro-preview
    if errorlevel 1 (
        echo ERROR: gemini-3.1-pro-preview benchmark failed twice.
    ) else (
        echo SUCCESS: gemini-3.1-pro-preview completed on retry.
    )
) else (
    echo SUCCESS: gemini-3.1-pro-preview completed.
)
echo.

:: ─────────────────────────────────────────────────────────────
:: Validate Results
:: ─────────────────────────────────────────────────────────────
echo ============================================================
echo   Validating benchmark quality...
echo ============================================================
echo.

echo Checking for API errors in benchmark CSVs...
for %%m in (o3 o3-mini gemini-3.1-pro-preview) do (
    echo Checking %%m...
    findstr /I /C:"ERROR" benchmarks\geo_multi_%%m_*.csv >nul 2>&1
    if errorlevel 1 (
        echo   [OK] %%m: No errors found
    ) else (
        echo   [WARNING] %%m: Contains API errors - check CSV file
        echo             File: benchmarks\geo_multi_%%m_*.csv
    )
)
echo.

:: ─────────────────────────────────────────────────────────────
:: Commit and Push
:: ─────────────────────────────────────────────────────────────
echo ============================================================
echo   Committing pulse benchmarks to GitHub...
echo ============================================================
git add benchmarks/*.csv
git commit -m "GEO pulse benchmark: %date:~-4%-%date:~4,2% | o3, o3-mini, Gemini 3.1 Pro Preview"
git push origin main
if errorlevel 1 (
    echo WARNING: git push failed. Check network connection or authentication.
    pause
    goto :skip_deploy
)

echo.
echo To update dashboard: Run trigger_paas_deploy.bat or manually pull from GitHub in PaaS UI

:skip_deploy

echo.
echo ============================================================
echo   DONE. Pulse benchmark complete.
echo
echo   Next Steps:
echo   1. Review CSVs for error rate:
echo      - benchmarks\geo_multi_o3_*.csv
echo      - benchmarks\geo_multi_o3-mini_*.csv
echo      - benchmarks\geo_multi_gemini-3.1-pro-preview_*.csv
echo
echo   2. If error rate is LOW (^<10%%):
echo      - Uncomment PULSE_MODELS in generate_session_json.py
echo      - Update with actual SOV percentages
echo      - Run: python generate_session_json.py --monthly
echo      - Commit and push
echo
echo   3. If error rate is HIGH (^>30%%):
echo      - Check CAAS_API_KEY is valid
echo      - Check VPN connection
echo      - Consider adding retry logic to geo_benchmark_multi_model.py
echo ============================================================
echo.
pause
