@echo off
REM ============================================================
REM FileMaker Export Trigger Script
REM ============================================================
REM
REM This script opens FileMaker and runs the export script.
REM Schedule to run at 2:00 AM via Windows Task Scheduler.
REM
REM NOTE: FileMaker Pro 9 command-line options are limited.
REM You may need to use AutoHotkey or similar for full automation.
REM
REM Alternative: Keep FileMaker open and use a FileMaker script
REM that runs on a schedule using the OnTimer script trigger.
REM
REM ============================================================

setlocal

REM === CONFIGURATION - EDIT THESE ===
set "FM_PATH=C:\Program Files\FileMaker\FileMaker Pro 9\FileMaker Pro.exe"
set "FM_DATABASE=C:\Path\To\Your\Database.fp7"
set "EXPORT_DIR=C:\FilemakerRevEHR\exports"

REM Create export directory if needed
if not exist "%EXPORT_DIR%" mkdir "%EXPORT_DIR%"

REM Log start
echo %DATE% %TIME% - Starting FileMaker export >> "%EXPORT_DIR%\..\logs\fm_export.log"

REM Option 1: Open FileMaker with the database
REM The export script should be set to run on database open
REM or triggered by an OnTimer event
start "" "%FM_PATH%" "%FM_DATABASE%"

REM Wait for FileMaker to complete (adjust time as needed)
REM timeout /t 300 /nobreak

echo %DATE% %TIME% - FileMaker export trigger complete >> "%EXPORT_DIR%\..\logs\fm_export.log"

REM Note: For fully automated exports, consider:
REM 1. Keeping FileMaker open 24/7 with OnTimer scripts
REM 2. Using FileMaker Server (supports scheduled scripts)
REM 3. Using AutoHotkey for GUI automation
