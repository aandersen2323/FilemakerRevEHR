@echo off
REM Monthly Report Sync Script
setlocal enabledelayedexpansion

set "PROJECT_DIR=C:\FilemakerRevEHR"
set "EXPORT_FILE=monthly_report.pdf"

cd /d "%PROJECT_DIR%"

echo Checking for PDF...
if not exist "exports\%EXPORT_FILE%" (
    echo ERROR: PDF not found at exports\%EXPORT_FILE%
    echo Run the AutoIt script first to export from FileMaker
    pause
    exit /b 1
)

echo Installing dependencies...
pip install pdfplumber pandas pyyaml google-auth google-api-python-client -q

echo Processing PDF and uploading to Google Sheets...
python -m src.monthly_report --pdf "exports\%EXPORT_FILE%"

if %ERRORLEVEL% neq 0 (
    echo FAILED
    pause
    exit /b 1
)

echo SUCCESS!
pause
