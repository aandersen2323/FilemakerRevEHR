@echo off
REM ============================================================
REM FileMaker RevEHR Setup Test Script
REM ============================================================
REM
REM Run this script to verify your setup is correct before
REM enabling the nightly automation.
REM
REM ============================================================

echo.
echo ============================================================
echo   FileMaker RevEHR Setup Test
echo ============================================================
echo.

set "ERRORS=0"

REM === Check Node.js ===
echo [TEST] Checking Node.js...
where node >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "tokens=*" %%v in ('node --version') do echo        OK: Node.js %%v found
) else (
    echo        FAIL: Node.js not found
    echo        Install from: https://nodejs.org
    set /a ERRORS+=1
)

REM === Check Python ===
echo [TEST] Checking Python...
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo        OK: %%v found
) else (
    echo        FAIL: Python not found
    echo        Install from: https://python.org
    set /a ERRORS+=1
)

REM === Check Directory Structure ===
echo [TEST] Checking directory structure...

if exist "scripts\cleanup_export.js" (
    echo        OK: scripts\cleanup_export.js found
) else (
    echo        FAIL: scripts\cleanup_export.js not found
    set /a ERRORS+=1
)

if exist "scripts\nightly_sync.bat" (
    echo        OK: scripts\nightly_sync.bat found
) else (
    echo        FAIL: scripts\nightly_sync.bat not found
    set /a ERRORS+=1
)

if exist "src\sync.py" (
    echo        OK: src\sync.py found
) else (
    echo        WARN: src\sync.py not found (may need setup)
)

if exist "config\settings.yaml" (
    echo        OK: config\settings.yaml found
) else (
    if exist "config\settings.example.yaml" (
        echo        WARN: config\settings.yaml not found
        echo              Copy settings.example.yaml to settings.yaml and edit
    ) else (
        echo        FAIL: config\settings.yaml not found
        set /a ERRORS+=1
    )
)

REM === Check Exports Directory ===
echo [TEST] Checking exports directory...
if not exist "exports" (
    mkdir exports
    echo        CREATED: exports\ directory
) else (
    echo        OK: exports\ directory exists
)

if not exist "logs" (
    mkdir logs
    echo        CREATED: logs\ directory
) else (
    echo        OK: logs\ directory exists
)

REM === Test Cleanup Script ===
echo [TEST] Testing cleanup script...
node scripts\cleanup_export.js >nul 2>&1
if %ERRORLEVEL% equ 1 (
    echo        OK: cleanup_export.js runs correctly
) else (
    echo        FAIL: cleanup_export.js has errors
    set /a ERRORS+=1
)

REM === Check for Export Files ===
echo [TEST] Checking for export files...
if exist "exports\patients_raw.csv" (
    echo        OK: exports\patients_raw.csv found
) else if exist "exports\patients_clean.csv" (
    echo        OK: exports\patients_clean.csv found
) else (
    echo        INFO: No patient export files yet
    echo              Run FileMaker export first
)

if exist "exports\transactions_raw.csv" (
    echo        OK: exports\transactions_raw.csv found
) else if exist "exports\transactions_clean.csv" (
    echo        OK: exports\transactions_clean.csv found
) else if exist "trans.csv" (
    echo        OK: trans.csv found (test file)
) else (
    echo        INFO: No transaction export files yet
    echo              Run FileMaker export first
)

REM === Summary ===
echo.
echo ============================================================
if %ERRORS% equ 0 (
    echo   ALL TESTS PASSED!
    echo.
    echo   Next steps:
    echo   1. Export data from FileMaker to exports\ folder
    echo   2. Run: scripts\nightly_sync.bat
    echo   3. Set up Windows Task Scheduler
) else (
    echo   %ERRORS% TEST(S) FAILED
    echo.
    echo   Fix the issues above before proceeding.
)
echo ============================================================
echo.

pause
