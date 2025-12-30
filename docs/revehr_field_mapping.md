# RevolutionEHR Field Mapping Reference

This document maps FileMaker export fields to RevolutionEHR import fields based on official RevEHR documentation.

---

## Patient Demographics

### FileMaker → RevEHR Mapping

| FileMaker Field | RevEHR Field | Notes |
|-----------------|--------------|-------|
| Patient ID | `external_patient_id` | Use as external reference |
| First Name | `first_name` | Required |
| Middle Name | `middle_name` | |
| Last Name | `last_name` | Required |
| Birth Date | `date_of_birth` | Format: YYYY-MM-DD |
| Gender | `gender` | M/F → male/female |
| Cell Phone | `cell_phone` | |
| Home Phone | `home_phone` | |
| Work Phone | `work_phone` | |
| Email | `email` | |
| Street Address | `address_1` | |
| Address Line 2 | `address_2` | |
| City | `city` | |
| State | `state` | 2-letter code |
| Zip | `postal_code` | |
| SSN | `ssn` | If available |
| Notes | `general_note` | |

### RevEHR Patient Object Structure

```json
{
  "first_name": "John",
  "middle_name": "Robert",
  "last_name": "Smith",
  "suffix": "",
  "nickname": "",
  "date_of_birth": "1990-05-15",
  "gender": "male",
  "ssn": "",
  "marital_status": "",
  "address_1": "123 Main Street",
  "address_2": "Apt 4B",
  "city": "Oak Park",
  "state": "IL",
  "postal_code": "60301",
  "home_phone": "708-555-1234",
  "work_phone": "",
  "cell_phone": "708-555-5678",
  "email": "jsmith@email.com",
  "general_note": "",
  "primary_provider": "",
  "primary_location": "",
  "external_patient_id": "7081608"
}
```

---

## Contact Lens Rx

### FileMaker → RevEHR Mapping

| FileMaker Field | RevEHR Field | Notes |
|-----------------|--------------|-------|
| Transaction Date | `rx_date` | Format: YYYY-MM-DD |
| Expiration Date | `expiration_date` | Optional |
| Patient ID# | `patient_id` | RevEHR patient ID (from mapping) |
| **OD (Right Eye)** | | |
| Contact Lenses OD | `od_product_name` | Brand/product name |
| Base Curve OD | `od_base_curve` | e.g., "8.6" |
| Diameter OD | `od_diameter` | e.g., "14.2" |
| CL Sph OD | `od_sphere` | e.g., "-5.25" |
| CL Cyl OD | `od_cylinder` | e.g., "-0.75" |
| CL Axis OD | `od_axis` | e.g., "180" |
| CL Add OD | `od_add` | e.g., "+2.00" |
| **OS (Left Eye)** | | |
| Contact Lenses OS | `os_product_name` | Brand/product name |
| Base Curve OS | `os_base_curve` | |
| Diameter OS | `os_diameter` | |
| CL Sph OS | `os_sphere` | |
| CL Cyl OS | `os_cylinder` | |
| CL Axis OS | `os_axis` | |
| CL Add OS | `os_add` | |

### RevEHR CL Rx Object Structure

```json
{
  "patient_id": "revehr-patient-uuid",
  "rx_date": "2025-12-13",
  "expiration_date": "2026-12-13",
  "od_sphere": "-5.00",
  "od_cylinder": "",
  "od_axis": "",
  "od_add": "",
  "od_base_curve": "8.6",
  "od_diameter": "14.2",
  "od_product_name": "Biofinity Energys(6-pack)",
  "od_lens_type": "soft",
  "os_sphere": "-5.75",
  "os_cylinder": "",
  "os_axis": "",
  "os_add": "",
  "os_base_curve": "8.6",
  "os_diameter": "14.2",
  "os_product_name": "Biofinity Energys(6-pack)",
  "os_lens_type": "soft"
}
```

---

## Spectacle Rx (Glasses)

### RevEHR Spec Rx Fields

| RevEHR Field | Description |
|--------------|-------------|
| `sphere` | Sphere power (OD/OS separate records?) |
| `cylinder` | Cylinder power |
| `axis` | Axis in degrees |
| `add` | Add power for multifocals |
| `prism` | Prism power |
| `prism_orientation` | Prism direction |
| `rx_date` | Prescription date |
| `patient_id` | RevEHR patient ID |
| `distance_pd` | Distance PD |
| `near_pd` | Near PD |
| `exp_date` | Expiration date |

---

## Insurance

### RevEHR Insurance Fields

| RevEHR Field | Description |
|--------------|-------------|
| `company_name` | Insurance company |
| `policy_number` | Policy # |
| `group_number` | Group # |
| `plan_name` | Plan name |
| `plan_type` | Plan type |
| `priority` | Primary/Secondary |
| `effective_date` | Coverage start |
| `patient_id` | RevEHR patient ID |

---

## Data Format Requirements

### Dates
- Format: `YYYY-MM-DD` (ISO 8601)
- Example: `2025-12-30`

### Phone Numbers
- Format: `XXX-XXX-XXXX` or `(XXX) XXX-XXXX`
- Include area code

### Gender
- Values: `male`, `female`, or empty

### State
- 2-letter abbreviation: `IL`, `CA`, `NY`, etc.

### Numeric Values (Rx)
- Sphere: signed decimal, e.g., `-5.25`, `+2.00`
- Cylinder: signed decimal, e.g., `-0.75`
- Axis: integer 1-180
- Add: signed decimal, e.g., `+2.00`
- Base Curve: decimal, e.g., `8.6`
- Diameter: decimal, e.g., `14.2`

---

## API Notes

Based on RevEHR documentation, the system supports:

1. **Patient Import** - Create/update patient demographics
2. **CL Rx Import** - Create contact lens prescriptions linked to patients
3. **Spec Rx Import** - Create spectacle prescriptions
4. **External Patient ID** - Use FileMaker ID as external reference for matching

### Patient Matching Strategy

1. First sync: Create patient in RevEHR, store returned ID
2. Subsequent syncs: Use stored RevEHR ID for updates
3. Fallback: Search by name + DOB if ID not found

### CL Rx Deduplication

Use `Transaction_Num` from FileMaker as external reference to prevent duplicate Rx records.
