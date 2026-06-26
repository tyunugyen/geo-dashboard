@echo off
REM GEO Fill Session - Run after skeleton generation
REM This runs on the local machine with full CaaS access

echo ============================================
echo GEO Fill Session - %date% %time%
echo ============================================
echo.

cd /d C:\Users\tyunguyen\geo-dashboard

echo [1/3] Pulling latest from GitHub...
git fetch origin
git reset --hard origin/main
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: git reset failed with code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)
echo.

echo [2/3] Running fill_session.py...
python fill_session.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: fill_session.py failed with code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)
echo.

echo [3/3] Committing filled session.json...
python -c "import json; s=json.load(open('public/data/session.json', encoding='utf-8-sig')); print('  run_id:', s['meta']['run_id']); print('  perplexity:', len(s.get('perplexity_simulation', []))); print('  amplify:', len(s.get('amplify_threads', []))); print('  cite:', len(s.get('cite_pipeline', [])))"
git add public/data/session.json
git commit -m "[local-fill] GEO session filled via local scheduled task"
git push origin main
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: git push failed with code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ============================================
echo SUCCESS: Fill session complete
echo Dashboard updating via GitHub webhook
echo ============================================
echo.
