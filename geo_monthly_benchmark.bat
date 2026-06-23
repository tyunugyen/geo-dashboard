@echo off
:: ================================================================
:: GEO Monthly Benchmark — runs 1st Monday of each month
:: Runs Claude + GPT-4o + Gemini via GoCode proxy
:: Commits results to GitHub → PaaS redeploys → dashboard updates
:: ================================================================
echo.
echo ============================================================
echo   GEO Monthly Benchmark
echo   %DATE% %TIME%
echo ============================================================
echo.

:: Navigate to repo
cd /d C:\Users\tyunguyen\geo-dashboard

:: Check VPN / proxy reachable
echo Checking GoCode connection...
curl -s --max-time 5 -o nul -w "%%{http_code}" https://caas-gocode-prod.caas-prod.prod.onkatana.net > nul 2>&1
if errorlevel 1 (
    echo ERROR: Cannot reach GoCode proxy. Make sure you are on VPN.
    echo Run this script again after connecting to VPN.
    pause
    exit /b 1
)
echo GoCode reachable. Proceeding...
echo.

:: Run multi-model benchmark (Claude + GPT-4o + Gemini)
echo Running benchmark: Claude + GPT-4o + Gemini
echo This takes ~15-20 minutes...
python geo_benchmark_multi_model.py --models claude openai gemini --quiet
if errorlevel 1 (
    echo ERROR: Benchmark failed. Check CAAS_API_KEY is set.
    pause
    exit /b 1
)
echo Benchmark complete.
echo.

:: Push results to dashboard
echo Updating dashboard and pushing to GitHub...
python update_dashboard.py
if errorlevel 1 (
    echo WARNING: Dashboard update failed. Try: git pull --rebase origin main then re-run.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   DONE. Dashboard updated and pushed to GitHub.
echo   View at: https://host.beta.godaddy.com/paas/projects/kz6jwep09q
echo ============================================================
echo.
echo Next step: Open a GEO session in Claude for:
echo   - Perplexity citation audit (run top 10 prompts via web search)
echo   - AUDIT scorecard generation
echo   - STRATEGY brief update
echo   - Monthly report
echo.
