# Nightly Automation Setup Guide

## Overview

This guide walks you through setting up automated nightly sync from FileMaker Pro 9 to RevolutionEHR.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     NIGHTLY SYNC WORKFLOW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  2:00 AM    FileMaker exports data to CSV files                     │
│      │                                                              │
│      ▼                                                              │
│  exports/patients_raw.csv                                           │
│  exports/transactions_raw.csv                                       │
│      │                                                              │
│      ▼                                                              │
│  2:30 AM    nightly_sync.bat runs                                   │
│      │                                                              │
│      ├──► cleanup_export.js (adds headers, removes empty rows)      │
│      │                                                              │
│      ├──► python -m src.sync (uploads to RevEHR API)                │
│      │                                                              │
│      └──► Archives raw files, logs results                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: FileMaker Export Scripts

### Step 1: Create Export Layouts

You've already done this for Transactions. Also create for Patients:

**Patients Export Layout:**
- 14 fields in order (see docs/filemaker_tables_needed.md)

**Transactions Export Layout:**
- 41 fields in order (already created and tested)

### Step 2: Create FileMaker Export Scripts

In FileMaker, go to **Scripts → ScriptMaker** and create:

#### Script: "Nightly Export - Patients"
```
Go to Layout ["Patients Export List"]
Show All Records
Export Records [No dialog; "C:\FilemakerRevEHR\exports\patients_raw.csv"; Character Set: UTF-8; Field Order: Current Layout]
```

#### Script: "Nightly Export - Transactions"
```
Go to Layout ["Transactions Export"]
Show All Records
Export Records [No dialog; "C:\FilemakerRevEHR\exports\transactions_raw.csv"; Character Set: UTF-8; Field Order: Current Layout]
```

#### Script: "Nightly Export - All"
```
Perform Script ["Nightly Export - Patients"]
Perform Script ["Nightly Export - Transactions"]
```

### Step 3: Schedule FileMaker Export

**Option A: OnTimer Script Trigger (Recommended)**

FileMaker Pro 9 can use OnTimer to run scripts at intervals. Set up the database to:

1. Create a startup script that installs an OnTimer trigger
2. The timer checks if it's 2:00 AM and runs the export

```
# Startup Script
Install OnTimer Script ["Check Export Time"; Interval: 60]  # Check every 60 seconds

# Check Export Time Script
Set Variable [$hour; Get(CurrentTime)]
If [$hour = Time(2;0;0)]
    Perform Script ["Nightly Export - All"]
End If
```

**Option B: Manual Daily Export**

If automation is difficult, run exports manually each morning:
1. Open FileMaker
2. Run "Nightly Export - All" script
3. Run `nightly_sync.bat`

---

## Part 2: Windows Task Scheduler Setup

### Schedule the Sync Script

1. **Open Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create New Task**
   - Click "Create Task" (not "Create Basic Task")

3. **General Tab**
   - Name: `FileMaker RevEHR Sync`
   - Description: `Nightly sync from FileMaker to RevolutionEHR`
   - Select: "Run whether user is logged on or not"
   - Check: "Run with highest privileges"

4. **Triggers Tab**
   - Click "New"
   - Begin the task: "On a schedule"
   - Settings: Daily
   - Start: 2:30:00 AM
   - Recur every: 1 day
   - Check: Enabled

5. **Actions Tab**
   - Click "New"
   - Action: "Start a program"
   - Program/script: `C:\FilemakerRevEHR\scripts\nightly_sync.bat`
   - Start in: `C:\FilemakerRevEHR`

6. **Conditions Tab**
   - Uncheck: "Start the task only if the computer is on AC power"
   - This ensures it runs on laptops even on battery

7. **Settings Tab**
   - Check: "Allow task to be run on demand"
   - Check: "Run task as soon as possible after a scheduled start is missed"
   - Check: "If the task fails, restart every: 5 minutes"
   - Attempt to restart up to: 3 times

8. **Click OK** and enter your Windows password

---

## Part 3: Directory Structure

Ensure this structure exists on your Windows machine:

```
C:\FilemakerRevEHR\
├── config\
│   └── settings.yaml          # RevEHR API credentials
├── exports\
│   ├── patients_raw.csv       # FileMaker exports here
│   ├── transactions_raw.csv   # FileMaker exports here
│   ├── patients_clean.csv     # Cleaned output
│   ├── transactions_clean.csv # Cleaned output
│   └── archive\               # Old exports archived here
│       └── 2025-12-30\
├── logs\
│   ├── sync_2025-12-30.log    # Daily sync logs
│   └── fm_export.log          # FileMaker export log
├── scripts\
│   ├── cleanup_export.js      # CSV cleanup script
│   ├── nightly_sync.bat       # Main automation script
│   └── filemaker_export.bat   # FM trigger (optional)
├── src\
│   └── ...                    # Python sync code
└── requirements.txt
```

---

## Part 4: Configuration

### Edit nightly_sync.bat

Update these paths at the top of the file:

```batch
set "PROJECT_DIR=C:\FilemakerRevEHR"
```

### Edit config/settings.yaml

```yaml
revehr:
  api_url: "https://api.revolutionehr.com/v1"
  api_key: "your-api-key-here"
  practice_id: "your-practice-id"

filemaker:
  exports_dir: "exports"
  patients_file: "patients_clean.csv"
  transactions_file: "transactions_clean.csv"

sync:
  dry_run: false           # Set true to test without uploading
  batch_size: 100          # Records per API call
  log_level: "INFO"
```

---

## Part 5: Testing

### Test 1: Manual Export

1. In FileMaker, run "Nightly Export - All"
2. Check that files appear in `C:\FilemakerRevEHR\exports\`

### Test 2: Manual Sync

1. Open Command Prompt as Administrator
2. Run:
   ```cmd
   cd C:\FilemakerRevEHR
   scripts\nightly_sync.bat
   ```
3. Check the log file in `logs\`

### Test 3: Task Scheduler Test

1. In Task Scheduler, right-click your task
2. Click "Run"
3. Check History tab for results
4. Check log files

---

## Part 6: Monitoring

### Check Daily Logs

Logs are saved to `logs\sync_YYYY-MM-DD.log`

**Successful sync log:**
```
============================================================
FileMaker to RevEHR Sync - 2025-12-30 02:30:00
============================================================

[02:30:00] Starting nightly sync...
[02:30:01] Checking prerequisites...
[02:30:01] Checking export files...
[OK] Found: patients_raw.csv
[OK] Found: transactions_raw.csv
[02:30:02] Cleaning patients export...
[OK] Patients cleaned successfully
[02:30:03] Cleaning transactions export...
[OK] Transactions cleaned successfully
[02:30:04] Starting RevEHR sync...
[OK] RevEHR sync completed successfully
[02:30:15] Archiving raw export files...
[OK] Raw files archived

[02:30:15] ============================================
[02:30:15] SYNC COMPLETED SUCCESSFULLY
[02:30:15] ============================================
```

### Email Alerts (Optional)

Add to the end of `nightly_sync.bat` to get email notifications:

```batch
REM === EMAIL NOTIFICATION ===
REM Requires blat.exe or similar command-line email tool
REM blat "%LOGFILE%" -to admin@yourpractice.com -subject "RevEHR Sync %DATESTAMP%" -server smtp.yourserver.com
```

---

## Troubleshooting

### "No export files found"

- FileMaker export didn't run or failed
- Check FileMaker is open and the script ran
- Verify export path matches `EXPORTS_DIR` in batch file

### "Node.js not found"

- Install Node.js from https://nodejs.org
- Restart computer after installation
- Verify: Open CMD and type `node --version`

### "Python not found"

- Install Python from https://python.org
- Check "Add to PATH" during installation
- Verify: Open CMD and type `python --version`

### "RevEHR sync failed"

- Check `config/settings.yaml` has correct API credentials
- Verify API key is valid and not expired
- Check RevEHR API status
- Look at detailed error in log file

### Task doesn't run

- Ensure "Run whether user is logged on or not" is selected
- Computer must be powered on at scheduled time
- Check Task Scheduler History for errors

---

## Quick Reference

| Time | Action |
|------|--------|
| 2:00 AM | FileMaker exports to CSV |
| 2:30 AM | nightly_sync.bat runs |
| 2:30 AM | → Cleanup scripts run |
| 2:31 AM | → RevEHR sync runs |
| 2:35 AM | → Files archived, logs saved |

| File | Purpose |
|------|---------|
| `exports/patients_raw.csv` | Fresh FileMaker export |
| `exports/patients_clean.csv` | With headers, cleaned |
| `logs/sync_YYYY-MM-DD.log` | Daily sync log |
| `exports/archive/YYYY-MM-DD/` | Historical exports |
