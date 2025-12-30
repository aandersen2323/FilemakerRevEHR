@echo off
REM ============================================================
REM FileMaker to RevEHR Nightly Sync Script
REM ============================================================
REM
REM Schedule this script to run via Windows Task Scheduler
REM Recommended time: 2:30 AM (after FileMaker exports at 2:00 AM)
REM
REM Prerequisites:
REM   1. Node.js installed
REM   2. Python 3 installed
REM   3. FileMaker exports completed to exports\ folder
REM
REM ============================================================

setlocal enabledelayedexpansion

REM === CONFIGURATION ===
set "PROJECT_DIR=C:\FilemakerRevEHR"
set "EXPORTS_DIR=%PROJECT_DIR%\exports"
set "LOGS_DIR=%PROJECT_DIR%\logs"
set "SCRIPTS_DIR=%PROJECT_DIR%\scripts"

REM Export file names (must match FileMaker export script output)
set "PATIENTS_RAW=patients_raw.csv"
set "TRANSACTIONS_RAW=transactions_raw.csv"

REM Cleaned file names
set "PATIENTS_CLEAN=patients_clean.csv"
set "TRANSACTIONS_CLEAN=transactions_clean.csv"

REM === SETUP ===
cd /d "%PROJECT_DIR%"

REM Create logs directory if needed
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"

REM Log file with timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "DATESTAMP=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%"
set "TIMESTAMP=%dt:~8,2%:%dt:~10,2%:%dt:~12,2%"
set "LOGFILE=%LOGS_DIR%\sync_%DATESTAMP%.log"

REM === START LOGGING ===
echo ============================================================ >> "%LOGFILE%"
echo FileMaker to RevEHR Sync - %DATESTAMP% %TIMESTAMP% >> "%LOGFILE%"
echo ============================================================ >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo [%TIMESTAMP%] Starting nightly sync... >> "%LOGFILE%"
echo Starting nightly sync...

REM === CHECK PREREQUISITES ===
echo [%TIME%] Checking prerequisites... >> "%LOGFILE%"

REM Check Node.js
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js not found in PATH >> "%LOGFILE%"
    echo ERROR: Node.js not found. Please install Node.js.
    goto :error
)

REM Check Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found in PATH >> "%LOGFILE%"
    echo ERROR: Python not found. Please install Python 3.
    goto :error
)

REM === CHECK EXPORT FILES ===
echo [%TIME%] Checking export files... >> "%LOGFILE%"

set "PATIENTS_EXISTS=0"
set "TRANSACTIONS_EXISTS=0"

if exist "%EXPORTS_DIR%\%PATIENTS_RAW%" (
    set "PATIENTS_EXISTS=1"
    echo [OK] Found: %PATIENTS_RAW% >> "%LOGFILE%"
) else (
    echo [WARN] Not found: %PATIENTS_RAW% >> "%LOGFILE%"
)

if exist "%EXPORTS_DIR%\%TRANSACTIONS_RAW%" (
    set "TRANSACTIONS_EXISTS=1"
    echo [OK] Found: %TRANSACTIONS_RAW% >> "%LOGFILE%"
) else (
    echo [WARN] Not found: %TRANSACTIONS_RAW% >> "%LOGFILE%"
)

if "%PATIENTS_EXISTS%"=="0" if "%TRANSACTIONS_EXISTS%"=="0" (
    echo [ERROR] No export files found! >> "%LOGFILE%"
    echo ERROR: No export files found. Check FileMaker export script.
    goto :error
)

REM === CLEANUP PATIENTS ===
if "%PATIENTS_EXISTS%"=="1" (
    echo [%TIME%] Cleaning patients export... >> "%LOGFILE%"
    echo Cleaning patients export...

    node "%SCRIPTS_DIR%\cleanup_export.js" "%EXPORTS_DIR%\%PATIENTS_RAW%" "%EXPORTS_DIR%\%PATIENTS_CLEAN%" --add-headers >> "%LOGFILE%" 2>&1

    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Patients cleanup failed >> "%LOGFILE%"
        echo ERROR: Patients cleanup failed
    ) else (
        echo [OK] Patients cleaned successfully >> "%LOGFILE%"
    )
)

REM === CLEANUP TRANSACTIONS ===
if "%TRANSACTIONS_EXISTS%"=="1" (
    echo [%TIME%] Cleaning transactions export... >> "%LOGFILE%"
    echo Cleaning transactions export...

    node "%SCRIPTS_DIR%\cleanup_export.js" "%EXPORTS_DIR%\%TRANSACTIONS_RAW%" "%EXPORTS_DIR%\%TRANSACTIONS_CLEAN%" --add-headers --type=transactions >> "%LOGFILE%" 2>&1

    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Transactions cleanup failed >> "%LOGFILE%"
        echo ERROR: Transactions cleanup failed
    ) else (
        echo [OK] Transactions cleaned successfully >> "%LOGFILE%"
    )
)

REM === RUN REVEHR SYNC ===
echo [%TIME%] Starting RevEHR sync... >> "%LOGFILE%"
echo Starting RevEHR sync...

python -m src.sync >> "%LOGFILE%" 2>&1

if %ERRORLEVEL% neq 0 (
    echo [ERROR] RevEHR sync failed with error code %ERRORLEVEL% >> "%LOGFILE%"
    echo ERROR: RevEHR sync failed. Check log for details.
    goto :error
)

echo [OK] RevEHR sync completed successfully >> "%LOGFILE%"

REM === ARCHIVE RAW FILES ===
echo [%TIME%] Archiving raw export files... >> "%LOGFILE%"

set "ARCHIVE_DIR=%EXPORTS_DIR%\archive\%DATESTAMP%"
if not exist "%ARCHIVE_DIR%" mkdir "%ARCHIVE_DIR%"

if exist "%EXPORTS_DIR%\%PATIENTS_RAW%" (
    move "%EXPORTS_DIR%\%PATIENTS_RAW%" "%ARCHIVE_DIR%\" >> "%LOGFILE%" 2>&1
)
if exist "%EXPORTS_DIR%\%TRANSACTIONS_RAW%" (
    move "%EXPORTS_DIR%\%TRANSACTIONS_RAW%" "%ARCHIVE_DIR%\" >> "%LOGFILE%" 2>&1
)

echo [OK] Raw files archived to %ARCHIVE_DIR% >> "%LOGFILE%"

REM === SUCCESS ===
echo. >> "%LOGFILE%"
echo [%TIME%] ============================================ >> "%LOGFILE%"
echo [%TIME%] SYNC COMPLETED SUCCESSFULLY >> "%LOGFILE%"
echo [%TIME%] ============================================ >> "%LOGFILE%"
echo.
echo Sync completed successfully!
echo Log file: %LOGFILE%
goto :end

:error
echo. >> "%LOGFILE%"
echo [%TIME%] ============================================ >> "%LOGFILE%"
echo [%TIME%] SYNC FAILED - CHECK LOG FOR DETAILS >> "%LOGFILE%"
echo [%TIME%] ============================================ >> "%LOGFILE%"
echo.
echo SYNC FAILED - Check log: %LOGFILE%
exit /b 1

:end
exit /b 0
