@echo off
:: ================================================================
:: GEO Monthly Benchmark — runs 1st of each month
:: Runs ALL available models via GoCode proxy
:: Commits results to GitHub → PaaS redeploys → dashboard updates
:: ================================================================
echo.
echo ============================================================
echo   GEO Monthly Benchmark (All Models)
echo   %DATE% %TIME%
echo ============================================================
echo.

cd /d C:\Users\tyunguyen\geo-dashboard

echo Running benchmark: ALL models (Claude + GPT + Gemini + o3 + more)...
echo This takes ~30-40 minutes for all models...
python geo_benchmark_multi_model.py --models all --quiet
if errorlevel 1 (
    echo Trying with core 3 models instead...
    python geo_benchmark_multi_model.py --models claude openai gemini --quiet
    if errorlevel 1 (
        echo ERROR: Benchmark failed. Check CAAS_API_KEY and VPN.
        pause
        exit /b 1
    )
)
echo Benchmark complete.
echo.

:: Push comparison CSV to dashboard (auto-detected)
echo Updating dashboard and pushing to GitHub...
python update_dashboard.py
if errorlevel 1 (
    git pull --rebase origin main
    python update_dashboard.py
)

echo.
echo ============================================================
echo   DONE. Dashboard updated and pushed to GitHub.
echo   View: https://host.beta.godaddy.com/paas/projects/kz6jwep09q
echo ============================================================
echo.
echo ── COPY THIS into Claude for your monthly GEO session ──────
python -c "import json,os; d=json.load(open('public/data.json')); print(f'\nRun monthly GEO session.\n\nRun ID: {d[\"meta\"][\"run_id\"]}\nPeriod: {d[\"meta\"][\"period\"]}\nModels: {d[\"meta\"][\"models\"]}\nUnaided SOV: {d[\"kpis\"][\"unaided_sov\"][\"value\"]} ({d[\"meta\"].get(\"prompt_count\",70)} prompts)\nAided SOV: {d[\"kpis\"][\"aided_sov\"][\"value\"]}\nRate Saver: {d[\"kpis\"][\"tech_health\"][\"value\"]}\n')"
echo ─────────────────────────────────────────────────────────────
echo.
