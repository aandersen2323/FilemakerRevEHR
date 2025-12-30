"""Contact lens prescription data models."""

from datetime import date
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class Eye(str, Enum):
    """Eye designation."""
    OD = "OD"  # Right eye (Oculus Dexter)
    OS = "OS"  # Left eye (Oculus Sinister)


class LensType(str, Enum):
    """Contact lens types."""
    SOFT = "soft"
    RGP = "rgp"  # Rigid Gas Permeable
    HYBRID = "hybrid"
    SCLERAL = "scleral"
    ORTHO_K = "ortho_k"


class WearSchedule(str, Enum):
    """Contact lens wear schedule."""
    DAILY = "daily_disposable"
    BI_WEEKLY = "bi_weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    EXTENDED_WEAR = "extended_wear"


class ContactLensEye(BaseModel):
    """Contact lens prescription for a single eye."""

    eye: Eye = Field(..., description="Which eye (OD/OS)")

    # Power/Sphere
    sphere: Optional[float] = Field(
        None,
        description="Sphere power in diopters",
        ge=-30.0,
        le=30.0
    )

    # Cylinder and Axis (for toric lenses)
    cylinder: Optional[float] = Field(
        None,
        description="Cylinder power for astigmatism",
        ge=-10.0,
        le=10.0
    )
    axis: Optional[int] = Field(
        None,
        description="Axis in degrees (1-180)",
        ge=1,
        le=180
    )

    # Add power (for multifocal/bifocal lenses)
    add_power: Optional[float] = Field(
        None,
        description="Add power for near vision",
        ge=0.0,
        le=4.0
    )
    add_designation: Optional[str] = Field(
        None,
        description="Add designation (Low, Med, High, or specific value)"
    )

    # Lens parameters
    base_curve: Optional[float] = Field(
        None,
        description="Base curve in mm",
        ge=6.0,
        le=10.0
    )
    diameter: Optional[float] = Field(
        None,
        description="Lens diameter in mm",
        ge=8.0,
        le=18.0
    )

    # Lens identification
    brand: Optional[str] = Field(None, description="Contact lens brand name")
    manufacturer: Optional[str] = Field(None, description="Lens manufacturer")
    product_name: Optional[str] = Field(None, description="Specific product name")

    # Color (if applicable)
    color: Optional[str] = Field(None, description="Lens color if enhancement/cosmetic")

    class Config:
        use_enum_values = True


class ContactLensRx(BaseModel):
    """Complete contact lens prescription."""

    # Reference IDs
    filemaker_id: Optional[str] = Field(None, description="FileMaker record ID")
    revehr_id: Optional[str] = Field(None, description="RevolutionEHR Rx ID")
    patient_filemaker_id: Optional[str] = Field(None, description="Patient's FileMaker ID")
    patient_revehr_id: Optional[str] = Field(None, description="Patient's RevolutionEHR ID")

    # Prescription details
    od: Optional[ContactLensEye] = Field(None, description="Right eye prescription")
    os: Optional[ContactLensEye] = Field(None, description="Left eye prescription")

    # Lens type and wear
    lens_type: LensType = Field(default=LensType.SOFT, description="Type of contact lens")
    wear_schedule: Optional[WearSchedule] = Field(None, description="Replacement schedule")

    # Prescription info
    prescriber: Optional[str] = Field(None, description="Prescribing doctor")
    exam_date: Optional[date] = Field(None, description="Date of exam")
    expiration_date: Optional[date] = Field(None, description="Rx expiration date")

    # Quantities
    boxes_od: Optional[int] = Field(None, description="Number of boxes for OD")
    boxes_os: Optional[int] = Field(None, description="Number of boxes for OS")

    # Notes
    fitting_notes: Optional[str] = Field(None, description="Fitting notes")
    special_instructions: Optional[str] = Field(None, description="Special instructions")

    # Status
    is_trial: bool = Field(default=False, description="Trial lens vs final Rx")
    is_current: bool = Field(default=True, description="Current active prescription")

    class Config:
        use_enum_values = True

    @property
    def is_toric(self) -> bool:
        """Check if prescription includes toric correction."""
        od_toric = self.od and self.od.cylinder is not None
        os_toric = self.os and self.os.cylinder is not None
        return od_toric or os_toric

    @property
    def is_multifocal(self) -> bool:
        """Check if prescription is multifocal."""
        od_multi = self.od and self.od.add_power is not None
        os_multi = self.os and self.os.add_power is not None
        return od_multi or os_multi
