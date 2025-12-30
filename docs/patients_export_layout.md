# FileMaker Patients Export Layout Guide

## Overview

This guide explains how to create a FileMaker Patients export layout for the RevolutionEHR sync. The layout exports patient demographics to a CSV file without headers (FileMaker Pro 9 limitation).

## Recommended Layout: 14 Columns (Simplified)

For basic patient sync, use this simplified 14-column layout:

| Column | Field Name | FileMaker Field | RevEHR Field | Required |
|--------|------------|-----------------|--------------|----------|
| 0 | Patient_ID | Patient ID | filemaker_id | Yes |
| 1 | First_Name | First Name | first_name | Yes |
| 2 | Last_Name | Last Name | last_name | Yes |
| 3 | DOB | Birth Date | date_of_birth | Yes |
| 4 | Address_1 | Street Address | street1 | No |
| 5 | Address_2 | Address Line 2 | street2 | No |
| 6 | City | City | city | No |
| 7 | State | State | state | No |
| 8 | Zip | Zip Code | postal_code | No |
| 9 | Home_Phone | Home Phone | home_phone | No |
| 10 | Cell_Phone | Cell Phone | mobile_phone | No |
| 11 | Work_Phone | Work Phone | work_phone | No |
| 12 | Email | Email | email | No |
| 13 | Notes | Notes | notes | No |

---

## Step-by-Step: Create the Export Layout

### Step 1: Open Layout Mode

1. Open your FileMaker database
2. Go to **View → Layout Mode** (or press Ctrl+L)
3. Click **Layouts → New Layout/Report**

### Step 2: Create New Layout

1. Layout Name: `Patients Export List`
2. Select: **Blank layout** or **Columnar list/report**
3. Click **Next**

### Step 3: Select Fields (In Order!)

Add these fields from the Patients table in EXACT order:

```
1.  Patient ID        (your primary key field)
2.  First Name
3.  Last Name
4.  Birth Date        (or DOB, Date of Birth)
5.  Street Address    (Address 1)
6.  Address Line 2    (if exists, otherwise leave blank)
7.  City
8.  State
9.  Zip Code
10. Home Phone
11. Cell Phone        (or Mobile Phone)
12. Work Phone
13. Email
14. Notes             (optional)
```

### Step 4: Layout View Settings

1. Switch to **List View** (View → View as List)
2. Remove any portal fields
3. Remove any summary fields
4. Make sure only body fields are included

---

## Creating the Export Script

In FileMaker, go to **Scripts → ScriptMaker** and create:

### Script: "Export Patients"

```
# FileMaker Script Steps:

Go to Layout ["Patients Export List"]
Show All Records
Sort Records [Restore; No dialog]    # Optional: sort by Patient ID
Export Records [No dialog;
    "C:\FilemakerRevEHR\exports\patients_raw.csv";
    Character Set: UTF-8;
    Field Order: Current Layout]
```

### Export Settings

When setting up the Export Records step:

1. **File Type:** Comma-Separated Text (.csv)
2. **Character Set:** UTF-8 (or Unicode UTF-8)
3. **Field Names:** Do NOT export field names (uncheck if option exists)
4. **Field Order:** Use the layout field order

---

## Full Layout: 68 Columns (Comprehensive)

If you want to export all patient fields, use the comprehensive mapping from `config/settings.yaml`:

| Column | RevEHR Field | Description |
|--------|--------------|-------------|
| 0 | age | Calculated age |
| 1 | balance | Account balance |
| 5 | date_of_birth | Birth date |
| 10 | city | City |
| 17 | email | Email address |
| 21 | first_name | First name |
| 24 | home_phone | Home phone |
| 27 | last_name | Last name |
| 36 | filemaker_id | Patient ID (PRIMARY KEY) |
| 37 | gender | Gender (M/F) |
| 53 | state | State |
| 54 | street1 | Street address |
| 65 | postal_code | Zip code |

See `config/settings.yaml` field_mappings.patient for the complete mapping.

---

## Testing the Export

### Manual Test

1. In FileMaker, run the "Export Patients" script
2. Check `C:\FilemakerRevEHR\exports\patients_raw.csv`
3. Open in a text editor to verify:
   - 14 columns (or your chosen column count)
   - No header row
   - Proper comma separation
   - UTF-8 encoding

### Cleanup Script

After export, run the cleanup script to add headers:

```cmd
cd C:\FilemakerRevEHR
node scripts\cleanup_export.js exports\patients_raw.csv exports\patients_clean.csv --add-headers
```

### Expected Output

**patients_raw.csv** (no headers):
```
7081608,John,Smith,1990-05-15,123 Main St,,Oak Park,IL,60301,555-1234,555-5678,,jsmith@email.com,
```

**patients_clean.csv** (with headers):
```
Patient_ID,First_Name,Last_Name,DOB,Address_1,Address_2,City,State,Zip,Home_Phone,Cell_Phone,Work_Phone,Email,Notes
7081608,John,Smith,1990-05-15,123 Main St,,Oak Park,IL,60301,555-1234,555-5678,,jsmith@email.com,
```

---

## Date Format Notes

FileMaker exports dates in various formats. The sync script handles:

- `M-D-YYYY` (e.g., 4-19-1965)
- `M/D/YYYY` (e.g., 7/1/1971)
- `YYYY-MM-DD` (ISO format)

Configure additional formats in `config/settings.yaml`:

```yaml
transformations:
  date_formats:
    - "%m-%d-%Y"
    - "%m/%d/%Y"
    - "%Y-%m-%d"
```

---

## Troubleshooting

### "File has wrong number of columns"

- Check that your layout has exactly 14 fields (or matches your config)
- Remove any portal fields or calculations
- Verify field order matches the expected mapping

### "Date parse error"

- Check date format in export matches config
- Empty dates should be empty strings, not "0" or "null"

### "Patient ID is empty"

- Ensure Patient ID field is first in your layout
- Check that all records have a Patient ID

### "Encoding issues / special characters"

- Export as UTF-8
- If FileMaker Pro 9 doesn't support UTF-8, use Windows-1252 and update config:
  ```yaml
  filemaker:
    exports:
      encoding: "windows-1252"
  ```
