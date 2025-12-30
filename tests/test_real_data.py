"""Test patient extraction with real FileMaker data."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from filemaker.file_reader import FileReader
from filemaker.extractor import FileMakerExtractor, ExtractionMethod


# Field mapping from settings.yaml - column position to field name
PATIENT_FIELD_MAPPING = {
    0: "age",
    1: "balance",
    3: "balance_secondary",
    4: "balance_tertiary",
    5: "date_of_birth",
    6: "cell_phone",
    9: "emergency_contact",
    10: "city",
    11: "patient_type",
    12: "clrx_status",
    14: "first_visit_date",
    16: "doctor",
    17: "email",
    19: "last_visit_date",
    21: "first_name",
    22: "cl_release_date",
    23: "parent_guardian",
    24: "home_phone",
    26: "recall_date",
    27: "last_name",
    31: "middle_name",
    32: "notes",
    33: "billing_notes",
    34: "occupation",
    35: "office_code",
    36: "filemaker_id",
    37: "gender",
    38: "preferred_name",
    39: "recall_due_date",
    40: "last_exam_type",
    51: "ssn",
    52: "spouse",
    53: "state",
    54: "street1",
    55: "title",
    57: "next_appointment",
    58: "insurance",
    63: "work_phone",
    65: "postal_code",
    66: "file_date",
    67: "office_name",
}


def test_file_reader_positional():
    """Test reading the andersen.csv file with positional mapping."""
    reader = FileReader(encoding="utf-8")

    file_path = Path(__file__).parent.parent / "andersen.csv"
    if not file_path.exists():
        print(f"Test file not found: {file_path}")
        return False

    print(f"Reading: {file_path}")
    print(f"Mapping {len(PATIENT_FIELD_MAPPING)} fields...")

    records = reader.read_csv_positional(
        str(file_path),
        field_mapping=PATIENT_FIELD_MAPPING,
        skip_empty_rows=True,
    )

    print(f"\nFound {len(records)} patient records")
    print("-" * 60)

    # Show first 5 patients
    for i, patient in enumerate(records[:5]):
        print(f"\nPatient {i+1}:")
        print(f"  ID: {patient.get('filemaker_id')}")
        print(f"  Name: {patient.get('title', '')} {patient.get('first_name')} {patient.get('middle_name', '')} {patient.get('last_name')}")
        print(f"  DOB: {patient.get('date_of_birth')}")
        print(f"  Gender: {patient.get('gender')}")
        print(f"  Address: {patient.get('street1')}, {patient.get('city')}, {patient.get('state')} {patient.get('postal_code')}")
        print(f"  Home Phone: {patient.get('home_phone')}")
        print(f"  Email: {patient.get('email')}")
        print(f"  Insurance: {patient.get('insurance')}")
        print(f"  Doctor: {patient.get('doctor')}")
        print(f"  Last Visit: {patient.get('last_visit_date')}")

    print("\n" + "=" * 60)
    print("DATA QUALITY CHECK")
    print("=" * 60)

    # Count populated fields
    field_counts = {}
    for record in records:
        for field, value in record.items():
            if field.startswith("_"):
                continue
            if field not in field_counts:
                field_counts[field] = 0
            if value is not None and value != "":
                field_counts[field] += 1

    print(f"\nField population rates ({len(records)} records):")
    for field, count in sorted(field_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(records)) * 100
        print(f"  {field}: {count}/{len(records)} ({pct:.0f}%)")

    return True


def test_extractor():
    """Test the full extractor with positional mapping."""
    file_path = Path(__file__).parent.parent / "andersen.csv"
    if not file_path.exists():
        print(f"Test file not found: {file_path}")
        return False

    extractor = FileMakerExtractor(
        method=ExtractionMethod.FILE,
        no_header=True,
    )

    # Set the field mapping
    extractor.set_field_mapping("patient", PATIENT_FIELD_MAPPING)

    # Extract patients
    patients = extractor.get_patients(file_path=str(file_path))

    print(f"\nExtractor returned {len(patients)} patients")

    # Test finding by ID
    if patients:
        test_id = patients[0].get("filemaker_id")
        found = extractor.get_patient_by_id(
            test_id,
            file_path=str(file_path),
            id_field="filemaker_id"
        )
        if found:
            print(f"Successfully found patient by ID: {test_id}")
            print(f"  Name: {found.get('first_name')} {found.get('last_name')}")
        else:
            print(f"Failed to find patient by ID: {test_id}")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("FILEMAKER DATA EXTRACTION TEST")
    print("=" * 60)

    print("\n\n### TEST 1: FileReader Positional ###\n")
    test_file_reader_positional()

    print("\n\n### TEST 2: FileMakerExtractor ###\n")
    test_extractor()
