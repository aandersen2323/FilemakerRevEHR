# FileMaker Field Mapping Analysis

Based on analysis of `andersen.csv` export (27 patient records, 67 fields per record)

## Field Positions (0-indexed)

| Pos | Field Name | Sample Data | Notes |
|-----|------------|-------------|-------|
| 0 | Age | "44", "82", "31" | Calculated age |
| 1 | Balance | "0", "-10", "151" | Account balance |
| 2 | Unknown | "" | Always empty |
| 3 | Balance2 | "0", "-10", "-673.63" | Secondary balance? |
| 4 | Balance3 | "0", "-4540.47" | Third balance field? |
| 5 | Birth_Date | "4-19-1965", "7/1/1971" | Multiple date formats |
| 6 | Cell_Phone_Alt | "816-651-6223" | Sometimes cell phone |
| 7 | Unknown | "" | Mostly empty |
| 8 | Unknown | "" | Mostly empty |
| 9 | Emergency_Contact | "None", "Jaxton" | Emergency contact name |
| 10 | City | "Olathe", "Overland Park" | City |
| 11 | Patient_Type | "CL Patient", "" | Contact Lens Patient flag |
| 12 | CLRx_Status | "CLRx Released" | CL prescription status |
| 13 | Unknown | "" | Empty |
| 14 | First_Visit_Date | "9/7/1998" | First visit date |
| 15 | Unknown | "" | Empty |
| 16 | Doctor | "Wes Johnson, O.D." | Primary doctor |
| 17 | Email | "nesrednadivad@yahoo.com" | Patient email |
| 18 | Unknown | "" | Empty |
| 19 | Last_Visit_Date | "9/27/1999", "9/14/2024" | Last visit date |
| 20 | Unknown | "" | Empty |
| 21 | First_Name | "Jeff", "Sharon" | First name |
| 22 | CL_Release_Date | "9/27/1999" | Contact lens release date |
| 23 | Parent_Guardian | "Becca", "Austin" | Parent/guardian name |
| 24 | Home_Phone | "663-2457", "913-888-5344" | Home phone |
| 25 | Unknown | "" | Empty |
| 26 | Recall_Date | "6/22/2024" | Next recall date |
| 27 | Last_Name | "Andersen" | Last name |
| 28-30 | Unknown | "" | Empty |
| 31 | Middle_Name | "t", "L", "Grant", "Lynn" | Middle name/initial |
| 32 | Notes | Long text | Patient notes |
| 33 | Billing_Notes | Long text | Billing/insurance notes |
| 34 | Occupation | "Housewife", "pastor" | Occupation |
| 35 | Office_Code | "7" | Office/location code |
| 36 | Patient_ID | "7004843", "7006084" | **PRIMARY KEY** |
| 37 | Gender | "F", "M", "" | Gender |
| 38 | Preferred_Name | "jeff", "Cathy", "Becca" | Nickname |
| 39 | Recall_Due_Date | "9/26/2000" | Recall appointment due |
| 40 | Last_Exam_Type | "CL Exam", "Eye Exam" | Last exam type |
| 41 | Flag_1 | "X" | Unknown flag |
| 42-44 | Unknown | "" | Empty |
| 45 | Flag_2 | "X" | Unknown flag |
| 46-50 | Unknown | "" | Empty |
| 51 | SSN | "490-94-3432" | Social Security Number |
| 52 | Spouse | "David", "Melissa" | Spouse name |
| 53 | State | "KS", "MO", "NE" | State |
| 54 | Address | "14311 w. 115th terr" | Street address |
| 55 | Title | "Mr.", "Mrs.", "Dr." | Title/salutation |
| 56 | Newsletter_Flag | "T" | Newsletter subscription? |
| 57 | Next_Appt_Date | "9/27/1999" | Next appointment date |
| 58 | Insurance | "Medicare Supplement", "BCBS" | Primary insurance |
| 59-62 | Unknown | "" | Empty |
| 63 | Work_Phone | "319-6203", "913-381-5577" | Work phone |
| 64 | Unknown | "" | Empty |
| 65 | Zip | "66062", "66213" | Zip code |
| 66 | File_Date | "9/18/2008" | File/record creation date |
| 67 | Office_Name | "Professional Eyecare Oak Park, PA" | Office name |

## Key Fields for RevEHR Sync

### Required Patient Demographics
- **Patient_ID** (pos 36) - Primary key for matching
- **First_Name** (pos 21)
- **Last_Name** (pos 27)
- **Birth_Date** (pos 5) - Multiple formats: "M-D-YYYY", "M/D/YYYY"
- **Gender** (pos 37) - "M", "F", or empty
- **SSN** (pos 51)

### Contact Information
- **Address** (pos 54)
- **City** (pos 10)
- **State** (pos 53)
- **Zip** (pos 65)
- **Home_Phone** (pos 24)
- **Work_Phone** (pos 63)
- **Cell_Phone** (pos 6) - Sometimes populated
- **Email** (pos 17)

### Additional Demographics
- **Title** (pos 55)
- **Middle_Name** (pos 31)
- **Preferred_Name** (pos 38)
- **Spouse** (pos 52)
- **Emergency_Contact** (pos 9)
- **Occupation** (pos 34)

### Practice Information
- **Patient_Type** (pos 11) - "CL Patient" or blank
- **Doctor** (pos 16) - Primary provider
- **Office_Code** (pos 35)
- **First_Visit_Date** (pos 14)
- **Last_Visit_Date** (pos 19)
- **Last_Exam_Type** (pos 40)

### Insurance
- **Insurance** (pos 58) - Primary insurance name

### Notes
- **Notes** (pos 32) - Patient notes
- **Billing_Notes** (pos 33) - Billing history

## Data Quality Issues

1. **Phone numbers** - Some missing area codes (e.g., "663-2457")
2. **Date formats** - Mixed formats ("4-19-1965" vs "7/1/1971")
3. **Empty fields** - Many unused field positions
4. **Gender** - Sometimes empty, needs default handling
5. **Middle name** - Sometimes single letter, sometimes full name
