"""Patient demographic data models."""

from datetime import date
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, EmailStr


class Gender(str, Enum):
    """Patient gender options."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class PhoneType(str, Enum):
    """Phone number types."""
    HOME = "home"
    WORK = "work"
    MOBILE = "mobile"
    FAX = "fax"


class AddressType(str, Enum):
    """Address types."""
    HOME = "home"
    WORK = "work"
    BILLING = "billing"
    SHIPPING = "shipping"


class PhoneNumber(BaseModel):
    """Phone number with type."""
    number: str = Field(..., description="Phone number")
    type: PhoneType = Field(default=PhoneType.HOME, description="Type of phone")
    is_primary: bool = Field(default=False, description="Primary contact number")

    class Config:
        use_enum_values = True


class Address(BaseModel):
    """Physical address."""
    type: AddressType = Field(default=AddressType.HOME, description="Address type")
    street1: str = Field(..., description="Street address line 1")
    street2: Optional[str] = Field(None, description="Street address line 2")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/Province")
    postal_code: str = Field(..., description="ZIP/Postal code")
    country: str = Field(default="US", description="Country code")
    is_primary: bool = Field(default=False, description="Primary address")

    class Config:
        use_enum_values = True


class PatientDemographics(BaseModel):
    """Core patient demographic information."""
    first_name: str = Field(..., description="Patient first name")
    middle_name: Optional[str] = Field(None, description="Patient middle name")
    last_name: str = Field(..., description="Patient last name")
    preferred_name: Optional[str] = Field(None, description="Preferred/nickname")

    date_of_birth: date = Field(..., description="Date of birth")
    gender: Gender = Field(default=Gender.UNKNOWN, description="Patient gender")

    ssn: Optional[str] = Field(None, description="Social Security Number (last 4 or full)")

    email: Optional[EmailStr] = Field(None, description="Email address")

    class Config:
        use_enum_values = True


class Patient(BaseModel):
    """Complete patient record."""

    # Internal IDs
    filemaker_id: Optional[str] = Field(None, description="FileMaker record ID")
    revehr_id: Optional[str] = Field(None, description="RevolutionEHR patient ID")

    # Demographics
    demographics: PatientDemographics = Field(..., description="Patient demographics")

    # Contact information
    addresses: List[Address] = Field(default_factory=list, description="Patient addresses")
    phone_numbers: List[PhoneNumber] = Field(default_factory=list, description="Phone numbers")

    # Additional info
    emergency_contact_name: Optional[str] = Field(None, description="Emergency contact name")
    emergency_contact_phone: Optional[str] = Field(None, description="Emergency contact phone")
    emergency_contact_relationship: Optional[str] = Field(None, description="Relationship to patient")

    # Practice info
    preferred_location: Optional[str] = Field(None, description="Preferred practice location")
    preferred_provider: Optional[str] = Field(None, description="Preferred provider/doctor")
    referral_source: Optional[str] = Field(None, description="How patient heard about practice")

    # Status
    is_active: bool = Field(default=True, description="Active patient status")

    # Timestamps
    created_date: Optional[date] = Field(None, description="Record creation date")
    modified_date: Optional[date] = Field(None, description="Last modification date")

    class Config:
        use_enum_values = True

    @property
    def full_name(self) -> str:
        """Get patient's full name."""
        parts = [self.demographics.first_name]
        if self.demographics.middle_name:
            parts.append(self.demographics.middle_name)
        parts.append(self.demographics.last_name)
        return " ".join(parts)

    @property
    def primary_address(self) -> Optional[Address]:
        """Get primary address if available."""
        for addr in self.addresses:
            if addr.is_primary:
                return addr
        return self.addresses[0] if self.addresses else None

    @property
    def primary_phone(self) -> Optional[PhoneNumber]:
        """Get primary phone number if available."""
        for phone in self.phone_numbers:
            if phone.is_primary:
                return phone
        return self.phone_numbers[0] if self.phone_numbers else None
