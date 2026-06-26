@echo off
echo ============================================================
echo GEO Dashboard - Pre-Flight Check
echo Run this Sunday night to verify Monday automation will work
echo ============================================================
echo.

set ERRORS=0

:: Check 1: VPN Connection
echo [1/6] Checking VPN connection...
ping -n 1 internal-caas-endpoint.godaddy.com >nul 2>&1
if %errorLevel% EQU 0 (
    echo   [OK] VPN connected
) else (
    echo   [WARN] VPN not connected - REQUIRED for Monday
    set ERRORS=1
)

:: Check 2: CAAS_API_KEY
echo [2/6] Checking CAAS_API_KEY...
if defined CAAS_API_KEY (
    echo   [OK] CAAS_API_KEY is set
) else (
    echo   [FAIL] CAAS_API_KEY not set
    set ERRORS=1
)

:: Check 3: Python
echo [3/6] Checking Python...
python --version >nul 2>&1
if %errorLevel% EQU 0 (
    echo   [OK] Python found
) else (
    echo   [FAIL] Python not found in PATH
    set ERRORS=1
)

:: Check 4: Git
echo [4/6] Checking Git...
git --version >nul 2>&1
if %errorLevel% EQU 0 (
    echo   [OK] Git found
) else (
    echo   [FAIL] Git not found in PATH
    set ERRORS=1
)

:: Check 5: Scheduled Tasks
echo [5/6] Checking scheduled tasks...
schtasks /query /tn "GEO Weekly Benchmark" >nul 2>&1
if %errorLevel% EQU 0 (
    echo   [OK] GEO Weekly Benchmark task exists
) else (
    echo   [FAIL] GEO Weekly Benchmark task not found
    set ERRORS=1
)

schtasks /query /tn "GEO Fill Session (Weekly)" >nul 2>&1
if %errorLevel% EQU 0 (
    echo   [OK] GEO Fill Session (Weekly) task exists
) else (
    echo   [FAIL] GEO Fill Session (Weekly) task not found
    set ERRORS=1
)

:: Check 6: Power Settings
echo [6/6] Checking power settings...
powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE | findstr /C:"Current AC Power Setting Index: 0x00000000" >nul
if %errorLevel% EQU 0 (
    echo   [OK] Sleep disabled on AC power
) else (
    echo   [WARN] PC may sleep during tasks - run prevent_sleep_monday.bat
    set ERRORS=1
)

echo.
echo ============================================================
if %ERRORS% EQU 0 (
    echo   ✓ ALL CHECKS PASSED - Ready for Monday!
) else (
    echo   ✗ ISSUES FOUND - Fix before Monday
)
echo ============================================================
echo.
echo Next scheduled run:
schtasks /query /tn "GEO Weekly Benchmark" /fo LIST /v | findstr /i "NextRunTime"
echo.
pause
