"""Transaction model for FileMaker Transactions data."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


@dataclass
class ContactLensRx:
    """Contact Lens prescription data (one eye)."""

    lens_name: Optional[str] = None
    base_curve: Optional[str] = None
    diameter: Optional[str] = None
    sphere: Optional[str] = None
    cylinder: Optional[str] = None
    axis: Optional[str] = None
    add_power: Optional[str] = None
    quantity: Optional[int] = None

    def has_data(self) -> bool:
        """Check if this eye has any Rx data."""
        return bool(self.lens_name or self.sphere)


@dataclass
class Transaction:
    """
    FileMaker Transaction record.

    Contains financial transaction data and embedded Contact Lens Rx.
    """

    # Primary key
    transaction_num: str

    # Foreign key to Patients
    patient_id: str

    # Transaction date
    transaction_date: Optional[date] = None

    # Provider info
    doctor: Optional[str] = None
    exam_proc: Optional[str] = None
    cl_fitting_proc: Optional[str] = None
    expiration_date: Optional[date] = None

    # Contact Lens Rx - Primary
    cl_od: ContactLensRx = field(default_factory=ContactLensRx)
    cl_os: ContactLensRx = field(default_factory=ContactLensRx)

    # Contact Lens Rx - Secondary (alternate lenses)
    cl_od_alt: ContactLensRx = field(default_factory=ContactLensRx)
    cl_os_alt: ContactLensRx = field(default_factory=ContactLensRx)

    # Notes
    notes: Optional[str] = None

    def has_cl_rx(self) -> bool:
        """Check if this transaction has any contact lens Rx data."""
        return (
            self.cl_od.has_data() or
            self.cl_os.has_data() or
            self.cl_od_alt.has_data() or
            self.cl_os_alt.has_data() or
            bool(self.cl_fitting_proc)
        )

    def __str__(self) -> str:
        return f"Transaction({self.transaction_num}, Patient={self.patient_id}, Date={self.transaction_date})"


# Field mapping: CSV column index -> (field_name, parser_function)
# Based on the 38-column Transactions Export layout

def parse_date(value: str) -> Optional[date]:
    """Parse date from various formats."""
    if not value or not value.strip():
        return None
    value = value.strip().strip('"')

    # Try common formats
    for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%m/%d/%y']:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_int(value: str) -> Optional[int]:
    """Parse integer, return None if empty."""
    if not value or not value.strip():
        return None
    try:
        return int(float(value.strip().strip('"')))
    except (ValueError, TypeError):
        return None


def parse_str(value: str) -> Optional[str]:
    """Parse string, return None if empty."""
    if not value:
        return None
    value = value.strip().strip('"').strip()
    return value if value else None


# Positional field mapping for 38-column Transactions export
TRANSACTION_FIELD_MAPPING = {
    # Core Identity
    0: ('transaction_num', parse_str),
    1: ('patient_id', parse_str),
    2: ('transaction_date', parse_date),

    # Provider & Visit
    3: ('doctor', parse_str),
    4: ('exam_proc', parse_str),
    5: ('cl_fitting_proc', parse_str),
    6: ('expiration_date', parse_date),

    # CL OD - Primary
    7: ('cl_od.lens_name', parse_str),
    8: ('cl_od.base_curve', parse_str),
    9: ('cl_od.diameter', parse_str),
    10: ('cl_od.sphere', parse_str),
    11: ('cl_od.cylinder', parse_str),
    12: ('cl_od.axis', parse_str),
    13: ('cl_od.add_power', parse_str),
    14: ('cl_od.quantity', parse_int),

    # CL OS - Primary
    15: ('cl_os.lens_name', parse_str),
    16: ('cl_os.base_curve', parse_str),
    17: ('cl_os.diameter', parse_str),
    18: ('cl_os.sphere', parse_str),
    19: ('cl_os.cylinder', parse_str),
    20: ('cl_os.axis', parse_str),
    21: ('cl_os.add_power', parse_str),
    22: ('cl_os.quantity', parse_int),

    # CL OD - Secondary
    23: ('cl_od_alt.lens_name', parse_str),
    24: ('cl_od_alt.base_curve', parse_str),
    25: ('cl_od_alt.diameter', parse_str),
    26: ('cl_od_alt.sphere', parse_str),
    27: ('cl_od_alt.cylinder', parse_str),
    28: ('cl_od_alt.axis', parse_str),
    29: ('cl_od_alt.add_power', parse_str),

    # CL OS - Secondary
    30: ('cl_os_alt.lens_name', parse_str),
    31: ('cl_os_alt.base_curve', parse_str),
    32: ('cl_os_alt.diameter', parse_str),
    33: ('cl_os_alt.sphere', parse_str),
    34: ('cl_os_alt.cylinder', parse_str),
    35: ('cl_os_alt.axis', parse_str),
    36: ('cl_os_alt.add_power', parse_str),

    # Notes
    37: ('notes', parse_str),
}
