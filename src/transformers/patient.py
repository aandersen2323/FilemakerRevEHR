"""Patient data transformer.

Converts patient data between FileMaker format and RevolutionEHR API format.
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, List

from ..models.patient import (
    Patient,
    PatientDemographics,
    Address,
    PhoneNumber,
    Gender,
    PhoneType,
    AddressType,
)

logger = logging.getLogger(__name__)


class PatientTransformer:
    """Transform patient data between FileMaker and RevolutionEHR formats.

    Field mappings should be configured based on your specific
    FileMaker database schema.
    """

    # Default FileMaker to standard field mapping
    # Customize these based on your FileMaker schema
    DEFAULT_FIELD_MAP = {
        # Demographics
        "First Name": "first_name",
        "FirstName": "first_name",
        "Last Name": "last_name",
        "LastName": "last_name",
        "Middle Name": "middle_name",
        "MiddleName": "middle_name",
        "DOB": "date_of_birth",
        "Date of Birth": "date_of_birth",
        "DateOfBirth": "date_of_birth",
        "Gender": "gender",
        "Sex": "gender",
        "SSN": "ssn",
        "Social Security": "ssn",
        "Email": "email",
        "EmailAddress": "email",

        # Address
        "Address": "street1",
        "Address1": "street1",
        "Street": "street1",
        "Address2": "street2",
        "City": "city",
        "State": "state",
        "Zip": "postal_code",
        "ZipCode": "postal_code",
        "Postal Code": "postal_code",

        # Phone
        "Phone": "home_phone",
        "Home Phone": "home_phone",
        "HomePhone": "home_phone",
        "Work Phone": "work_phone",
        "WorkPhone": "work_phone",
        "Cell": "mobile_phone",
        "Cell Phone": "mobile_phone",
        "CellPhone": "mobile_phone",
        "Mobile": "mobile_phone",

        # IDs
        "PatientID": "filemaker_id",
        "Patient ID": "filemaker_id",
        "ID": "filemaker_id",
    }

    def __init__(self, field_map: Optional[Dict[str, str]] = None):
        """Initialize transformer with optional custom field mapping.

        Args:
            field_map: Custom FileMaker to standard field mapping
        """
        self.field_map = field_map or self.DEFAULT_FIELD_MAP

    def from_filemaker(self, fm_data: Dict[str, Any]) -> Patient:
        """Convert FileMaker record to Patient model.

        Args:
            fm_data: Raw FileMaker record dictionary

        Returns:
            Patient model instance
        """
        # Map fields
        mapped = self._map_fields(fm_data)

        # Parse date of birth
        dob = self._parse_date(mapped.get("date_of_birth"))
        if not dob:
            dob = date(1900, 1, 1)  # Default for missing DOB

        # Parse gender
        gender = self._parse_gender(mapped.get("gender"))

        # Create demographics
        demographics = PatientDemographics(
            first_name=mapped.get("first_name", "Unknown"),
            middle_name=mapped.get("middle_name"),
            last_name=mapped.get("last_name", "Unknown"),
            date_of_birth=dob,
            gender=gender,
            ssn=mapped.get("ssn"),
            email=mapped.get("email"),
        )

        # Create address if available
        addresses = []
        if mapped.get("street1") or mapped.get("city"):
            address = Address(
                type=AddressType.HOME,
                street1=mapped.get("street1", ""),
                street2=mapped.get("street2"),
                city=mapped.get("city", ""),
                state=mapped.get("state", ""),
                postal_code=mapped.get("postal_code", ""),
                is_primary=True,
            )
            addresses.append(address)

        # Create phone numbers
        phone_numbers = []
        if mapped.get("home_phone"):
            phone_numbers.append(
                PhoneNumber(
                    number=mapped["home_phone"],
                    type=PhoneType.HOME,
                    is_primary=True,
                )
            )
        if mapped.get("work_phone"):
            phone_numbers.append(
                PhoneNumber(
                    number=mapped["work_phone"],
                    type=PhoneType.WORK,
                )
            )
        if mapped.get("mobile_phone"):
            phone_numbers.append(
                PhoneNumber(
                    number=mapped["mobile_phone"],
                    type=PhoneType.MOBILE,
                )
            )

        return Patient(
            filemaker_id=str(mapped.get("filemaker_id")) if mapped.get("filemaker_id") else None,
            demographics=demographics,
            addresses=addresses,
            phone_numbers=phone_numbers,
        )

    def to_revehr(self, patient: Patient) -> Dict[str, Any]:
        """Convert Patient model to RevolutionEHR API format.

        Note: Adjust this based on actual RevolutionEHR API schema.

        Args:
            patient: Patient model instance

        Returns:
            Dictionary formatted for RevolutionEHR API
        """
        data = {
            "firstName": patient.demographics.first_name,
            "lastName": patient.demographics.last_name,
            "dateOfBirth": patient.demographics.date_of_birth.isoformat(),
        }

        if patient.demographics.middle_name:
            data["middleName"] = patient.demographics.middle_name

        if patient.demographics.gender != Gender.UNKNOWN:
            data["gender"] = patient.demographics.gender

        if patient.demographics.email:
            data["email"] = patient.demographics.email

        if patient.demographics.ssn:
            data["ssn"] = patient.demographics.ssn

        # Primary address
        if patient.primary_address:
            addr = patient.primary_address
            data["address"] = {
                "street1": addr.street1,
                "street2": addr.street2,
                "city": addr.city,
                "state": addr.state,
                "postalCode": addr.postal_code,
                "country": addr.country,
            }

        # Phone numbers
        phones = {}
        for phone in patient.phone_numbers:
            if phone.type == PhoneType.HOME:
                phones["homePhone"] = phone.number
            elif phone.type == PhoneType.WORK:
                phones["workPhone"] = phone.number
            elif phone.type == PhoneType.MOBILE:
                phones["mobilePhone"] = phone.number

        if phones:
            data["phones"] = phones

        # External ID reference
        if patient.filemaker_id:
            data["externalId"] = patient.filemaker_id

        return data

    def from_revehr(self, revehr_data: Dict[str, Any]) -> Patient:
        """Convert RevolutionEHR API response to Patient model.

        Args:
            revehr_data: RevolutionEHR API response

        Returns:
            Patient model instance
        """
        dob = self._parse_date(revehr_data.get("dateOfBirth"))

        demographics = PatientDemographics(
            first_name=revehr_data.get("firstName", ""),
            middle_name=revehr_data.get("middleName"),
            last_name=revehr_data.get("lastName", ""),
            date_of_birth=dob or date(1900, 1, 1),
            gender=self._parse_gender(revehr_data.get("gender")),
            email=revehr_data.get("email"),
            ssn=revehr_data.get("ssn"),
        )

        addresses = []
        if addr_data := revehr_data.get("address"):
            addresses.append(
                Address(
                    type=AddressType.HOME,
                    street1=addr_data.get("street1", ""),
                    street2=addr_data.get("street2"),
                    city=addr_data.get("city", ""),
                    state=addr_data.get("state", ""),
                    postal_code=addr_data.get("postalCode", ""),
                    is_primary=True,
                )
            )

        phone_numbers = []
        if phones := revehr_data.get("phones"):
            if phones.get("homePhone"):
                phone_numbers.append(
                    PhoneNumber(number=phones["homePhone"], type=PhoneType.HOME, is_primary=True)
                )
            if phones.get("workPhone"):
                phone_numbers.append(
                    PhoneNumber(number=phones["workPhone"], type=PhoneType.WORK)
                )
            if phones.get("mobilePhone"):
                phone_numbers.append(
                    PhoneNumber(number=phones["mobilePhone"], type=PhoneType.MOBILE)
                )

        return Patient(
            revehr_id=revehr_data.get("id"),
            filemaker_id=revehr_data.get("externalId"),
            demographics=demographics,
            addresses=addresses,
            phone_numbers=phone_numbers,
        )

    def _map_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply field mapping to raw data."""
        mapped = {}
        for fm_field, std_field in self.field_map.items():
            if fm_field in data:
                mapped[std_field] = data[fm_field]
        # Include any unmapped fields
        for key, value in data.items():
            if key not in self.field_map:
                mapped[key] = value
        return mapped

    def _parse_date(self, value: Any) -> Optional[date]:
        """Parse date from various formats."""
        if value is None:
            return None

        if isinstance(value, date):
            return value

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, str):
            # Try common formats
            formats = [
                "%Y-%m-%d",
                "%m/%d/%Y",
                "%m-%d-%Y",
                "%d/%m/%Y",
                "%Y/%m/%d",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue

        logger.warning(f"Could not parse date: {value}")
        return None

    def _parse_gender(self, value: Any) -> Gender:
        """Parse gender from various formats."""
        if value is None:
            return Gender.UNKNOWN

        value = str(value).lower().strip()

        if value in ("m", "male", "1"):
            return Gender.MALE
        if value in ("f", "female", "2"):
            return Gender.FEMALE
        if value in ("o", "other", "3"):
            return Gender.OTHER

        return Gender.UNKNOWN
