# FileMaker Tables Required for RevEHR Sync

## Export File Size Issue - SOLVED

Your export had **60MB for 27 records** because FileMaker exported portal/related data.

**Solution:** Use the cleanup script:
```bash
node scripts/cleanup_export.js andersen.csv exports/patients_clean.csv
# Result: 60MB -> 18KB (99.97% reduction)
```

Or **better** - export from a layout WITHOUT portals (see below).

---

## Current Status

### Patients Table - MAPPED
Source: `andersen.csv` (27 sample records analyzed)

**Key fields mapped:**
- Patient ID (primary key)
- Demographics (name, DOB, gender, SSN)
- Contact info (address, phone, email)
- Insurance
- Practice info (doctor, visit dates)

---

## Additional Tables Needed

Based on user's FileMaker database, these tables exist:

### Priority 1: Required for Core RevEHR Sync

#### Contact Lens Rx / CLOrders
**Purpose:** Sync contact lens prescriptions to RevEHR

**Fields needed:**
- Rx ID (primary key)
- Patient ID (foreign key to Patients)
- OD/OS: Sphere, Cylinder, Axis, Add
- OD/OS: Base Curve, Diameter
- OD/OS: Brand, Manufacturer, Product Name
- Lens Type (soft, RGP, hybrid, etc.)
- Prescriber name
- Exam date, Expiration date
- Fitting notes

**Export request:** Please export a sample from your CL Rx/Orders table

---

#### Glasses/Spectacle Rx
**Purpose:** Sync eyeglass prescriptions to RevEHR

**Fields needed:**
- Rx ID (primary key)
- Patient ID (foreign key to Patients)
- OD/OS: Sphere, Cylinder, Axis
- OD/OS: Add power
- OD/OS: Prism (horizontal/vertical)
- PD (monocular and binocular)
- Rx Type (distance, near, progressive, etc.)
- Prescriber name
- Exam date, Expiration date

**Export request:** Please export a sample from your Glasses Rx table

---

### Priority 2: Optional but Useful

#### Appointments
**Purpose:** Sync appointment history

**Fields likely needed:**
- Appointment ID
- Patient ID
- Date/Time
- Appointment type
- Provider
- Status (scheduled, completed, cancelled)
- Notes

---

#### Dispenses
**Purpose:** Track product dispensing for patient history

**Fields likely needed:**
- Dispense ID
- Patient ID
- Product info
- Date
- Quantity
- Price

---

### Priority 3: Not Needed for RevEHR Sync

These tables are likely internal to your practice:
- **email** - Internal communication logs
- **lookups** - Reference/dropdown data
- **open/openadmin/openmngr** - Access/session management
- **prodprices** - Internal pricing
- **recover** - Backup/recovery
- **timecards** - Staff time tracking

---

## How to Export Data

Since FileMaker Pro 9 doesn't allow direct exports with your current access, use copy/paste method:

1. Go to a **List View** layout showing the table data
2. `Records → Show All Records` to see all data
3. `Edit → Select All` (Ctrl+A)
4. `Edit → Copy` (Ctrl+C)
5. Paste into Excel/Google Sheets
6. Save as CSV

**Important:**
- Export includes field values but NOT column headers
- We map by column position, so field ORDER matters
- Export same fields in same order each time

---

## Running the Sync

Once tables are mapped:

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and edit config
cp config/settings.example.yaml config/settings.yaml
# Edit settings.yaml with your RevEHR API credentials

# Run sync
python -m src.sync                    # Full sync
python -m src.sync --patients-only    # Patients only
python -m src.sync --cl-rx-only       # Contact lens Rx only
python -m src.sync --glasses-rx-only  # Glasses Rx only
```

---

## Deployment Options

### Option A: Manual Nightly Run
1. Export data from FileMaker (copy/paste to CSV)
2. Place CSVs in `exports/` directory
3. Run sync script manually

### Option B: Scheduled (Recommended)
1. Set up FileMaker script to export data nightly
2. Use Windows Task Scheduler or cron to run sync
3. Logs saved to `logs/filemaker_revehr.log`

### Option C: Real-time (Requires FileMaker Server)
Would need FileMaker Server for ODBC access - not available with Pro 9

---

## Nightly Export Workflow for Multiple Databases

You mentioned having multiple databases: **patients, examd, transactions, appointments, clorders, dispenses**, etc.

### Recommended Nightly Process

**Step 1: Create Export Layouts in FileMaker**

For each table you want to sync, create a simple **List View** layout:
- NO portals
- NO related fields from other tables
- Just the fields from that one table

This prevents the 10,000 rows-per-record problem.

**Step 2: Create FileMaker Export Scripts**

```
Script: "Nightly Export - Patients"
  Go to Layout ["Patients List Export"]
  Show All Records
  Export Records [No dialog; "C:\exports\patients.csv"; CSV]

Script: "Nightly Export - Exams"
  Go to Layout ["Exams List Export"]
  Show All Records
  Export Records [No dialog; "C:\exports\exams.csv"; CSV]

Script: "Nightly Export - All"
  Perform Script ["Nightly Export - Patients"]
  Perform Script ["Nightly Export - Exams"]
  Perform Script ["Nightly Export - CLOrders"]
  ... etc
```

**Step 3: Schedule FileMaker Script**

FileMaker Pro 9 doesn't have built-in scheduling, so use Windows Task Scheduler:

1. Create a batch file `C:\scripts\run_fm_export.bat`:
```batch
@echo off
"C:\Program Files\FileMaker\FileMaker Pro 9\FileMaker Pro.exe" -f "C:\path\to\database.fp7" -s "Nightly Export - All"
```

2. Schedule in Windows Task Scheduler to run at 2:00 AM

**Step 4: Run Cleanup & Sync**

After FileMaker exports, run cleanup and sync:

```batch
@echo off
REM cleanup_and_sync.bat - Run at 2:30 AM (after FM export)

cd C:\FilemakerRevEHR

REM Clean up exports (remove portal bloat)
node scripts\cleanup_export.js exports\patients.csv exports\patients_clean.csv
node scripts\cleanup_export.js exports\exams.csv exports\exams_clean.csv

REM Run sync to RevEHR
python -m src.sync

REM Log completion
echo %date% %time% Sync completed >> logs\nightly_sync.log
```

### Files to Export Nightly for RevEHR

| FileMaker Table | Export File | RevEHR Entity |
|-----------------|-------------|---------------|
| Patients | patients.csv | Patients |
| Contact Lens Rx | clrx.csv | Contact Lens Rx |
| Glasses Rx | glassesrx.csv | Glasses Rx |
| Appointments | appointments.csv | Appointments (optional) |
| Exams | exams.csv | Clinical data (if supported) |

### Getting Cleaner Exports from FileMaker

The 60MB problem is caused by exporting from a layout with **portals**.

**To avoid this:**

1. Create a new layout for export only
2. Base it on the table you want (e.g., Patients)
3. Use **List View** (not Form View)
4. Add ONLY fields from that table (no portals, no related fields)
5. Export from this layout

**FileMaker Layout Tips:**
- `Layouts → New Layout/Report`
- Choose "Blank layout" or "List"
- Select only fields from the current table
- Name it "Patients Export List" or similar
