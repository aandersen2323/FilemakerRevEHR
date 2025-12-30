"""Contact lens prescription transformer.

Converts CL Rx data between FileMaker and RevolutionEHR formats.
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, Optional

from ..models.contact_lens_rx import (
    ContactLensRx,
    ContactLensEye,
    Eye,
    LensType,
    WearSchedule,
)

logger = logging.getLogger(__name__)


class ContactLensRxTransformer:
    """Transform contact lens Rx between FileMaker and RevolutionEHR formats."""

    DEFAULT_FIELD_MAP = {
        # IDs
        "RxID": "rx_id",
        "PatientID": "patient_id",

        # Right eye (OD)
        "OD_Sphere": "od_sphere",
        "OD_Cylinder": "od_cylinder",
        "OD_Axis": "od_axis",
        "OD_Add": "od_add",
        "OD_BC": "od_base_curve",
        "OD_Dia": "od_diameter",
        "OD_Brand": "od_brand",

        # Left eye (OS)
        "OS_Sphere": "os_sphere",
        "OS_Cylinder": "os_cylinder",
        "OS_Axis": "os_axis",
        "OS_Add": "os_add",
        "OS_BC": "os_base_curve",
        "OS_Dia": "os_diameter",
        "OS_Brand": "os_brand",

        # General
        "Prescriber": "prescriber",
        "ExamDate": "exam_date",
        "ExpDate": "expiration_date",
        "LensType": "lens_type",
        "WearSchedule": "wear_schedule",
        "Notes": "notes",
    }

    def __init__(self, field_map: Optional[Dict[str, str]] = None):
        """Initialize transformer."""
        self.field_map = field_map or self.DEFAULT_FIELD_MAP

    def from_filemaker(self, fm_data: Dict[str, Any]) -> ContactLensRx:
        """Convert FileMaker CL Rx to model.

        Args:
            fm_data: Raw FileMaker record

        Returns:
            ContactLensRx model
        """
        mapped = self._map_fields(fm_data)

        # Build OD eye
        od = None
        if any(mapped.get(f"od_{f}") for f in ["sphere", "cylinder", "base_curve"]):
            od = ContactLensEye(
                eye=Eye.OD,
                sphere=self._parse_float(mapped.get("od_sphere")),
                cylinder=self._parse_float(mapped.get("od_cylinder")),
                axis=self._parse_int(mapped.get("od_axis")),
                add_power=self._parse_float(mapped.get("od_add")),
                base_curve=self._parse_float(mapped.get("od_base_curve")),
                diameter=self._parse_float(mapped.get("od_diameter")),
                brand=mapped.get("od_brand"),
            )

        # Build OS eye
        os_eye = None
        if any(mapped.get(f"os_{f}") for f in ["sphere", "cylinder", "base_curve"]):
            os_eye = ContactLensEye(
                eye=Eye.OS,
                sphere=self._parse_float(mapped.get("os_sphere")),
                cylinder=self._parse_float(mapped.get("os_cylinder")),
                axis=self._parse_int(mapped.get("os_axis")),
                add_power=self._parse_float(mapped.get("os_add")),
                base_curve=self._parse_float(mapped.get("os_base_curve")),
                diameter=self._parse_float(mapped.get("os_diameter")),
                brand=mapped.get("os_brand"),
            )

        # Parse lens type
        lens_type = self._parse_lens_type(mapped.get("lens_type"))
        wear_schedule = self._parse_wear_schedule(mapped.get("wear_schedule"))

        return ContactLensRx(
            filemaker_id=str(mapped.get("rx_id")) if mapped.get("rx_id") else None,
            patient_filemaker_id=str(mapped.get("patient_id")) if mapped.get("patient_id") else None,
            od=od,
            os=os_eye,
            lens_type=lens_type,
            wear_schedule=wear_schedule,
            prescriber=mapped.get("prescriber"),
            exam_date=self._parse_date(mapped.get("exam_date")),
            expiration_date=self._parse_date(mapped.get("expiration_date")),
            fitting_notes=mapped.get("notes"),
        )

    def to_revehr(self, rx: ContactLensRx) -> Dict[str, Any]:
        """Convert ContactLensRx model to RevolutionEHR format.

        Args:
            rx: ContactLensRx model

        Returns:
            RevolutionEHR API format dict
        """
        data = {
            "lensType": rx.lens_type,
        }

        if rx.od:
            data["od"] = {
                "sphere": rx.od.sphere,
                "cylinder": rx.od.cylinder,
                "axis": rx.od.axis,
                "addPower": rx.od.add_power,
                "baseCurve": rx.od.base_curve,
                "diameter": rx.od.diameter,
                "brand": rx.od.brand,
                "manufacturer": rx.od.manufacturer,
            }

        if rx.os:
            data["os"] = {
                "sphere": rx.os.sphere,
                "cylinder": rx.os.cylinder,
                "axis": rx.os.axis,
                "addPower": rx.os.add_power,
                "baseCurve": rx.os.base_curve,
                "diameter": rx.os.diameter,
                "brand": rx.os.brand,
                "manufacturer": rx.os.manufacturer,
            }

        if rx.wear_schedule:
            data["wearSchedule"] = rx.wear_schedule

        if rx.prescriber:
            data["prescriber"] = rx.prescriber

        if rx.exam_date:
            data["examDate"] = rx.exam_date.isoformat()

        if rx.expiration_date:
            data["expirationDate"] = rx.expiration_date.isoformat()

        if rx.fitting_notes:
            data["notes"] = rx.fitting_notes

        if rx.filemaker_id:
            data["externalId"] = rx.filemaker_id

        return data

    def _map_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply field mapping."""
        mapped = {}
        for fm_field, std_field in self.field_map.items():
            if fm_field in data:
                mapped[std_field] = data[fm_field]
        return mapped

    def _parse_float(self, value: Any) -> Optional[float]:
        """Parse float value."""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_int(self, value: Any) -> Optional[int]:
        """Parse integer value."""
        if value is None or value == "":
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def _parse_date(self, value: Any) -> Optional[date]:
        """Parse date value."""
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return None

    def _parse_lens_type(self, value: Any) -> LensType:
        """Parse lens type."""
        if value is None:
            return LensType.SOFT
        value = str(value).lower()
        if "rgp" in value or "rigid" in value:
            return LensType.RGP
        if "hybrid" in value:
            return LensType.HYBRID
        if "scleral" in value:
            return LensType.SCLERAL
        if "ortho" in value:
            return LensType.ORTHO_K
        return LensType.SOFT

    def _parse_wear_schedule(self, value: Any) -> Optional[WearSchedule]:
        """Parse wear schedule."""
        if value is None:
            return None
        value = str(value).lower()
        if "daily" in value:
            return WearSchedule.DAILY
        if "bi-weekly" in value or "biweekly" in value or "2 week" in value:
            return WearSchedule.BI_WEEKLY
        if "month" in value:
            return WearSchedule.MONTHLY
        if "quarter" in value:
            return WearSchedule.QUARTERLY
        if "year" in value or "annual" in value:
            return WearSchedule.ANNUAL
        return None
