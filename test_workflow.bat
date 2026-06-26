@echo off
echo ============================================================
echo Testing GEO Dashboard Scheduled Task Workflow
echo ============================================================
echo.

echo [1/4] Running Weekly Benchmark...
echo   This will take ~12 minutes (Claude Sonnet only)
echo.
call geo_weekly_benchmark.bat
if %errorLevel% NEQ 0 (
    echo   [FAILED] Weekly benchmark failed!
    pause
    exit /b 1
)
echo   [OK] Weekly benchmark completed
echo.

echo [2/4] Running Fill Session...
echo   This will take ~3 minutes
echo.
call geo_fill_session.bat
if %errorLevel% NEQ 0 (
    echo   [FAILED] Fill session failed!
    pause
    exit /b 1
)
echo   [OK] Fill session completed
echo.

echo [3/4] Checking if session.json was updated...
if exist public\data\session.json (
    echo   [OK] session.json exists at public\data\session.json
    for %%A in (public\data\session.json) do echo   File size: %%~zA bytes
    echo   Last modified:
    forfiles /p public\data /m session.json /c "cmd /c echo   @fdate @ftime"
) else (
    echo   [FAILED] session.json not found at public\data\session.json!
    pause
    exit /b 1
)
echo.

echo [4/4] Checking if GitHub push happened (if configured)...
git log -1 --oneline 2>nul
if %errorLevel% EQU 0 (
    echo   [OK] Git repository detected
    echo   Latest commit:
    git log -1 --pretty=format:"   %%h - %%s (%%ar)" 2>nul
    echo.
    git status -s
) else (
    echo   [SKIP] Not a git repository or git not configured
)
echo.

echo ============================================================
echo Test Complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Review session.json to verify it contains benchmark data
echo 2. If GitHub auto-push is configured, check your repository
echo 3. Wait for scheduled run on Monday to verify automation
echo.
pause
