# Transactions Export Layout for RevEHR Sync

## Overview

The FileMaker **Transactions** table contains:
- Financial transaction records
- **Contact Lens Rx data** (embedded in each transaction)
- Exam/visit information
- Billing codes

## Recommended Export Fields (38 columns)

Create a List View layout in FileMaker with these fields **in this exact order**:

### Core Identity (3 fields)
| Position | Field Name | Purpose |
|----------|------------|---------|
| 0 | Transaction # | Primary key |
| 1 | Patient ID# | **Foreign key to Patients** |
| 2 | Transaction Date | Date of transaction |

### Provider & Visit (4 fields)
| Position | Field Name | Purpose |
|----------|------------|---------|
| 3 | Doctor | Prescriber name |
| 4 | Exam Proc | Exam procedure type |
| 5 | CL Fitting Proc | CL fitting type |
| 6 | Expiration Date | Rx expiration |

### Contact Lens OD - Primary (8 fields)
| Position | Field Name | Purpose |
|----------|------------|---------|
| 7 | Contact Lenses | OD lens brand/product |
| 8 | Base Curve | OD base curve |
| 9 | Diameter | OD diameter |
| 10 | CL Sph OD | OD sphere |
| 11 | CL Cyl OD | OD cylinder |
| 12 | CL Axis OD | OD axis |
| 13 | claddod | OD add power |
| 14 | Quant CL OD | OD quantity ordered |

### Contact Lens OS - Primary (8 fields)
| Position | Field Name | Purpose |
|----------|------------|---------|
| 15 | Contact LensesOS | OS lens brand/product |
| 16 | Base CurveOS | OS base curve |
| 17 | Diameter OS | OS diameter |
| 18 | CL Sph OS | OS sphere |
| 19 | CL Cyl OS | OS cylinder |
| 20 | CL Axis OS | OS axis |
| 21 | claddos | OS add power |
| 22 | Quant CL OS | OS quantity ordered |

### Contact Lens OD - Secondary (7 fields)
| Position | Field Name | Purpose |
|----------|------------|---------|
| 23 | Contact Lenses 1 | OD alternate lens |
| 24 | Base Curve 1 | OD alternate BC |
| 25 | Diameter 1 | OD alternate diameter |
| 26 | CL Sph OD1 | OD alternate sphere |
| 27 | CL Cyl OD1 | OD alternate cyl |
| 28 | CL Axis OD1 | OD alternate axis |
| 29 | claddod1 | OD alternate add |

### Contact Lens OS - Secondary (7 fields)
| Position | Field Name | Purpose |
|----------|------------|---------|
| 30 | Contact LensesOS 1 | OS alternate lens |
| 31 | Base CurveOS 1 | OS alternate BC |
| 32 | Diameter OS1 | OS alternate diameter |
| 33 | CL Sph OS1 | OS alternate sphere |
| 34 | CL Cyl OS1 | OS alternate cyl |
| 35 | CL Axis OS1 | OS alternate axis |
| 36 | claddos1 | OS alternate add |

### Notes (1 field)
| Position | Field Name | Purpose |
|----------|------------|---------|
| 37 | Notes | Transaction notes |

---

## Creating the Export Layout in FileMaker

### Step 1: Create New Layout
1. `Layouts` → `New Layout/Report`
2. Name: **"Transactions Export"**
3. Table: **Transactions**
4. Type: **List View** (or Columnar List)

### Step 2: Add Fields in Order
Add ONLY these 38 fields in the Body part:
- Drag fields from Field Picker in the exact order above
- **Do NOT add any portals or related fields**
- Keep it simple - just the fields listed

### Step 3: Create Export Script
```
Script: "Export Transactions"
  Go to Layout ["Transactions Export"]
  Show All Records
  Sort Records [Restore; No dialog]  // Optional: by Transaction Date
  Export Records [No dialog; "transactions.csv"; CSV]
```

---

## Filtering for CL Rx Records Only

Not all transactions have contact lens data. To export only CL-related records:

### Option A: Find Before Export
```
Script: "Export CL Transactions"
  Go to Layout ["Transactions Export"]
  Enter Find Mode []
  Set Field [Transactions::Contact Lenses; "*"]  // Has OD lens
  Or
  Set Field [Transactions::Contact LensesOS; "*"]  // Has OS lens
  Or
  Set Field [Transactions::CL Fitting Proc; "*"]  // Has CL fitting
  Perform Find []
  Export Records [No dialog; "cl_transactions.csv"; CSV]
```

### Option B: Export All, Filter in Python
Export everything and let the sync script filter for records with CL data.

---

## Sample Data Format

After export with headers added:
```csv
Transaction_Num,Patient_ID,Transaction_Date,Doctor,Exam_Proc,CL_Fitting_Proc,Expiration_Date,Contact_Lenses_OD,Base_Curve_OD,Diameter_OD,CL_Sph_OD,CL_Cyl_OD,CL_Axis_OD,CL_Add_OD,Quant_CL_OD,...
7566225,7000004,12/15/2025,"Dr. Smith","92014","CL Eval NPHW",12/15/2026,"Acuvue Oasys",8.4,14.0,-2.25,-0.75,180,+1.50,4,...
```

---

## Linking to Patients

The `Patient ID#` field in Transactions matches the `Patient ID` field in your Patients table.

Example relationship:
```
Transactions.Patient ID# = 7000004
     ↓ links to ↓
Patients.Patient_ID = 7000004 (Leonard Smith)
```

When syncing to RevEHR:
1. Look up patient in RevEHR by Patient ID (or name/DOB)
2. Create/update CL Rx record linked to that patient

---

## Notes

- **Secondary CL fields** (Contact Lenses 1, etc.) are for patients with different lenses for each eye or backup prescriptions
- **Quant CL** fields track quantity ordered (boxes), not Rx data
- Many transactions will have empty CL fields (exam-only visits)
- The **Expiration Date** field may need to be calculated if not populated
