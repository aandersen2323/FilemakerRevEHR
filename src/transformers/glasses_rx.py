"""Glasses prescription transformer.

Converts glasses Rx data between FileMaker and RevolutionEHR formats.
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, Optional

from ..models.glasses_rx import (
    GlassesRx,
    GlassesEye,
    Eye,
    RxType,
    PrismDirection,
)

logger = logging.getLogger(__name__)


class GlassesRxTransformer:
    """Transform glasses Rx between FileMaker and RevolutionEHR formats."""

    DEFAULT_FIELD_MAP = {
        # IDs
        "RxID": "rx_id",
        "PatientID": "patient_id",

        # Right eye (OD)
        "OD_Sphere": "od_sphere",
        "OD_Cylinder": "od_cylinder",
        "OD_Axis": "od_axis",
        "OD_Add": "od_add",
        "OD_Prism_H": "od_prism_h",
        "OD_Prism_H_Dir": "od_prism_h_dir",
        "OD_Prism_V": "od_prism_v",
        "OD_Prism_V_Dir": "od_prism_v_dir",
        "OD_VA": "od_va",
        "OD_PD": "od_pd",

        # Left eye (OS)
        "OS_Sphere": "os_sphere",
        "OS_Cylinder": "os_cylinder",
        "OS_Axis": "os_axis",
        "OS_Add": "os_add",
        "OS_Prism_H": "os_prism_h",
        "OS_Prism_H_Dir": "os_prism_h_dir",
        "OS_Prism_V": "os_prism_v",
        "OS_Prism_V_Dir": "os_prism_v_dir",
        "OS_VA": "os_va",
        "OS_PD": "os_pd",

        # Binocular
        "PD": "pd_distance",
        "PD_Near": "pd_near",

        # General
        "RxType": "rx_type",
        "Prescriber": "prescriber",
        "ExamDate": "exam_date",
        "ExpDate": "expiration_date",
        "Notes": "notes",
        "LensMaterial": "lens_material",
        "Treatments": "lens_treatments",
    }

    def __init__(self, field_map: Optional[Dict[str, str]] = None):
        """Initialize transformer."""
        self.field_map = field_map or self.DEFAULT_FIELD_MAP

    def from_filemaker(self, fm_data: Dict[str, Any]) -> GlassesRx:
        """Convert FileMaker glasses Rx to model.

        Args:
            fm_data: Raw FileMaker record

        Returns:
            GlassesRx model
        """
        mapped = self._map_fields(fm_data)

        # Build OD eye
        od = None
        if any(mapped.get(f"od_{f}") for f in ["sphere", "cylinder"]):
            od = GlassesEye(
                eye=Eye.OD,
                sphere=self._parse_float(mapped.get("od_sphere")),
                cylinder=self._parse_float(mapped.get("od_cylinder")),
                axis=self._parse_int(mapped.get("od_axis")),
                add_power=self._parse_float(mapped.get("od_add")),
                prism_horizontal=self._parse_float(mapped.get("od_prism_h")),
                prism_horizontal_direction=self._parse_prism_dir(mapped.get("od_prism_h_dir")),
                prism_vertical=self._parse_float(mapped.get("od_prism_v")),
                prism_vertical_direction=self._parse_prism_dir(mapped.get("od_prism_v_dir")),
                pd=self._parse_float(mapped.get("od_pd")),
                va_distance=mapped.get("od_va"),
            )

        # Build OS eye
        os_eye = None
        if any(mapped.get(f"os_{f}") for f in ["sphere", "cylinder"]):
            os_eye = GlassesEye(
                eye=Eye.OS,
                sphere=self._parse_float(mapped.get("os_sphere")),
                cylinder=self._parse_float(mapped.get("os_cylinder")),
                axis=self._parse_int(mapped.get("os_axis")),
                add_power=self._parse_float(mapped.get("os_add")),
                prism_horizontal=self._parse_float(mapped.get("os_prism_h")),
                prism_horizontal_direction=self._parse_prism_dir(mapped.get("os_prism_h_dir")),
                prism_vertical=self._parse_float(mapped.get("os_prism_v")),
                prism_vertical_direction=self._parse_prism_dir(mapped.get("os_prism_v_dir")),
                pd=self._parse_float(mapped.get("os_pd")),
                va_distance=mapped.get("os_va"),
            )

        rx_type = self._parse_rx_type(mapped.get("rx_type"))

        return GlassesRx(
            filemaker_id=str(mapped.get("rx_id")) if mapped.get("rx_id") else None,
            patient_filemaker_id=str(mapped.get("patient_id")) if mapped.get("patient_id") else None,
            od=od,
            os=os_eye,
            rx_type=rx_type,
            pd_distance=self._parse_float(mapped.get("pd_distance")),
            pd_near=self._parse_float(mapped.get("pd_near")),
            prescriber=mapped.get("prescriber"),
            exam_date=self._parse_date(mapped.get("exam_date")),
            expiration_date=self._parse_date(mapped.get("expiration_date")),
            lens_material=mapped.get("lens_material"),
            lens_treatments=mapped.get("lens_treatments"),
            notes=mapped.get("notes"),
        )

    def to_revehr(self, rx: GlassesRx) -> Dict[str, Any]:
        """Convert GlassesRx model to RevolutionEHR format.

        Args:
            rx: GlassesRx model

        Returns:
            RevolutionEHR API format dict
        """
        data = {
            "rxType": rx.rx_type,
        }

        if rx.od:
            od_data = {
                "sphere": rx.od.sphere,
                "cylinder": rx.od.cylinder,
                "axis": rx.od.axis,
            }
            if rx.od.add_power:
                od_data["addPower"] = rx.od.add_power
            if rx.od.prism_horizontal:
                od_data["prismHorizontal"] = rx.od.prism_horizontal
                od_data["prismHorizontalDirection"] = rx.od.prism_horizontal_direction
            if rx.od.prism_vertical:
                od_data["prismVertical"] = rx.od.prism_vertical
                od_data["prismVerticalDirection"] = rx.od.prism_vertical_direction
            if rx.od.pd:
                od_data["pd"] = rx.od.pd
            data["od"] = od_data

        if rx.os:
            os_data = {
                "sphere": rx.os.sphere,
                "cylinder": rx.os.cylinder,
                "axis": rx.os.axis,
            }
            if rx.os.add_power:
                os_data["addPower"] = rx.os.add_power
            if rx.os.prism_horizontal:
                os_data["prismHorizontal"] = rx.os.prism_horizontal
                os_data["prismHorizontalDirection"] = rx.os.prism_horizontal_direction
            if rx.os.prism_vertical:
                os_data["prismVertical"] = rx.os.prism_vertical
                os_data["prismVerticalDirection"] = rx.os.prism_vertical_direction
            if rx.os.pd:
                os_data["pd"] = rx.os.pd
            data["os"] = os_data

        if rx.pd_distance:
            data["pdDistance"] = rx.pd_distance
        if rx.pd_near:
            data["pdNear"] = rx.pd_near

        if rx.prescriber:
            data["prescriber"] = rx.prescriber

        if rx.exam_date:
            data["examDate"] = rx.exam_date.isoformat()

        if rx.expiration_date:
            data["expirationDate"] = rx.expiration_date.isoformat()

        if rx.lens_material:
            data["lensMaterial"] = rx.lens_material

        if rx.lens_treatments:
            data["lensTreatments"] = rx.lens_treatments

        if rx.notes:
            data["notes"] = rx.notes

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

    def _parse_rx_type(self, value: Any) -> RxType:
        """Parse Rx type."""
        if value is None:
            return RxType.DISTANCE
        value = str(value).lower()
        if "prog" in value:
            return RxType.PROGRESSIVE
        if "bifocal" in value:
            return RxType.BIFOCAL
        if "trifocal" in value:
            return RxType.TRIFOCAL
        if "near" in value or "reading" in value:
            return RxType.NEAR
        if "computer" in value:
            return RxType.COMPUTER
        return RxType.DISTANCE

    def _parse_prism_dir(self, value: Any) -> Optional[PrismDirection]:
        """Parse prism direction."""
        if value is None:
            return None
        value = str(value).upper()
        if value in ("BU", "BASE UP", "UP"):
            return PrismDirection.BASE_UP
        if value in ("BD", "BASE DOWN", "DOWN"):
            return PrismDirection.BASE_DOWN
        if value in ("BI", "BASE IN", "IN"):
            return PrismDirection.BASE_IN
        if value in ("BO", "BASE OUT", "OUT"):
            return PrismDirection.BASE_OUT
        return None
