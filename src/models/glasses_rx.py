"""Glasses/spectacle prescription data models."""

from datetime import date
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class Eye(str, Enum):
    """Eye designation."""
    OD = "OD"  # Right eye (Oculus Dexter)
    OS = "OS"  # Left eye (Oculus Sinister)


class PrismDirection(str, Enum):
    """Prism base direction."""
    BASE_UP = "BU"
    BASE_DOWN = "BD"
    BASE_IN = "BI"
    BASE_OUT = "BO"


class RxType(str, Enum):
    """Type of glasses prescription."""
    DISTANCE = "distance"
    NEAR = "near"
    BIFOCAL = "bifocal"
    TRIFOCAL = "trifocal"
    PROGRESSIVE = "progressive"
    COMPUTER = "computer"
    OCCUPATIONAL = "occupational"


class GlassesEye(BaseModel):
    """Glasses prescription for a single eye."""

    eye: Eye = Field(..., description="Which eye (OD/OS)")

    # Distance vision
    sphere: Optional[float] = Field(
        None,
        description="Sphere power in diopters",
        ge=-30.0,
        le=30.0
    )
    cylinder: Optional[float] = Field(
        None,
        description="Cylinder power in diopters",
        ge=-10.0,
        le=10.0
    )
    axis: Optional[int] = Field(
        None,
        description="Axis in degrees (1-180)",
        ge=1,
        le=180
    )

    # Near vision add
    add_power: Optional[float] = Field(
        None,
        description="Add power for near/intermediate",
        ge=0.0,
        le=4.0
    )

    # Prism correction
    prism_horizontal: Optional[float] = Field(
        None,
        description="Horizontal prism in prism diopters",
        ge=0.0,
        le=20.0
    )
    prism_horizontal_direction: Optional[PrismDirection] = Field(
        None,
        description="Horizontal prism base direction (BI/BO)"
    )
    prism_vertical: Optional[float] = Field(
        None,
        description="Vertical prism in prism diopters",
        ge=0.0,
        le=20.0
    )
    prism_vertical_direction: Optional[PrismDirection] = Field(
        None,
        description="Vertical prism base direction (BU/BD)"
    )

    # Measurements
    pd: Optional[float] = Field(
        None,
        description="Pupillary distance (monocular) in mm",
        ge=20.0,
        le=45.0
    )
    seg_height: Optional[float] = Field(
        None,
        description="Segment height in mm"
    )
    oc_height: Optional[float] = Field(
        None,
        description="Optical center height in mm"
    )

    # Visual acuity achieved
    va_distance: Optional[str] = Field(None, description="Distance VA (e.g., 20/20)")
    va_near: Optional[str] = Field(None, description="Near VA (e.g., 20/20)")

    class Config:
        use_enum_values = True


class GlassesRx(BaseModel):
    """Complete glasses/spectacle prescription."""

    # Reference IDs
    filemaker_id: Optional[str] = Field(None, description="FileMaker record ID")
    revehr_id: Optional[str] = Field(None, description="RevolutionEHR Rx ID")
    patient_filemaker_id: Optional[str] = Field(None, description="Patient's FileMaker ID")
    patient_revehr_id: Optional[str] = Field(None, description="Patient's RevolutionEHR ID")

    # Prescription details
    od: Optional[GlassesEye] = Field(None, description="Right eye prescription")
    os: Optional[GlassesEye] = Field(None, description="Left eye prescription")

    # Rx type
    rx_type: RxType = Field(default=RxType.DISTANCE, description="Type of prescription")

    # Binocular PD (if not using monocular)
    pd_distance: Optional[float] = Field(
        None,
        description="Binocular PD for distance in mm",
        ge=40.0,
        le=80.0
    )
    pd_near: Optional[float] = Field(
        None,
        description="Binocular PD for near in mm",
        ge=40.0,
        le=80.0
    )

    # Prescription info
    prescriber: Optional[str] = Field(None, description="Prescribing doctor")
    exam_date: Optional[date] = Field(None, description="Date of exam")
    expiration_date: Optional[date] = Field(None, description="Rx expiration date")

    # Lens recommendations
    lens_material: Optional[str] = Field(None, description="Recommended lens material")
    lens_design: Optional[str] = Field(None, description="Lens design recommendation")
    lens_treatments: Optional[str] = Field(None, description="Coatings/treatments")

    # Notes
    notes: Optional[str] = Field(None, description="Additional notes")
    dispensing_notes: Optional[str] = Field(None, description="Dispensing instructions")

    # Status
    is_current: bool = Field(default=True, description="Current active prescription")

    class Config:
        use_enum_values = True

    @property
    def has_cylinder(self) -> bool:
        """Check if prescription includes astigmatism correction."""
        od_cyl = self.od and self.od.cylinder is not None and self.od.cylinder != 0
        os_cyl = self.os and self.os.cylinder is not None and self.os.cylinder != 0
        return od_cyl or os_cyl

    @property
    def has_prism(self) -> bool:
        """Check if prescription includes prism."""
        od_prism = self.od and (
            self.od.prism_horizontal is not None or
            self.od.prism_vertical is not None
        )
        os_prism = self.os and (
            self.os.prism_horizontal is not None or
            self.os.prism_vertical is not None
        )
        return od_prism or os_prism

    @property
    def has_add(self) -> bool:
        """Check if prescription includes add power."""
        od_add = self.od and self.od.add_power is not None
        os_add = self.os and self.os.add_power is not None
        return od_add or os_add

    @property
    def is_progressive_candidate(self) -> bool:
        """Check if this Rx would typically be made as progressive."""
        return self.has_add and self.rx_type in [
            RxType.PROGRESSIVE,
            RxType.BIFOCAL,
            RxType.TRIFOCAL
        ]
