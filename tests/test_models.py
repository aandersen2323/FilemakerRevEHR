"""Tests for data models."""

import pytest
from datetime import date

from src.models.patient import (
    Patient,
    PatientDemographics,
    Address,
    PhoneNumber,
    Gender,
    PhoneType,
    AddressType,
)
from src.models.contact_lens_rx import (
    ContactLensRx,
    ContactLensEye,
    Eye,
    LensType,
)
from src.models.glasses_rx import (
    GlassesRx,
    GlassesEye,
    RxType,
)


class TestPatientModel:
    """Tests for Patient model."""

    def test_create_patient_basic(self):
        """Test creating a basic patient."""
        demographics = PatientDemographics(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 5, 15),
        )
        patient = Patient(demographics=demographics)

        assert patient.demographics.first_name == "John"
        assert patient.demographics.last_name == "Doe"
        assert patient.full_name == "John Doe"

    def test_patient_with_middle_name(self):
        """Test patient full name with middle name."""
        demographics = PatientDemographics(
            first_name="John",
            middle_name="Robert",
            last_name="Doe",
            date_of_birth=date(1990, 5, 15),
        )
        patient = Patient(demographics=demographics)

        assert patient.full_name == "John Robert Doe"

    def test_patient_with_address(self):
        """Test patient with address."""
        demographics = PatientDemographics(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 5, 15),
        )
        address = Address(
            street1="123 Main St",
            city="Springfield",
            state="IL",
            postal_code="62701",
            is_primary=True,
        )
        patient = Patient(demographics=demographics, addresses=[address])

        assert patient.primary_address is not None
        assert patient.primary_address.city == "Springfield"

    def test_patient_with_phones(self):
        """Test patient with phone numbers."""
        demographics = PatientDemographics(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 5, 15),
        )
        phones = [
            PhoneNumber(number="555-1234", type=PhoneType.HOME, is_primary=True),
            PhoneNumber(number="555-5678", type=PhoneType.MOBILE),
        ]
        patient = Patient(demographics=demographics, phone_numbers=phones)

        assert patient.primary_phone is not None
        assert patient.primary_phone.number == "555-1234"


class TestContactLensRxModel:
    """Tests for ContactLensRx model."""

    def test_create_cl_rx(self):
        """Test creating contact lens Rx."""
        od = ContactLensEye(
            eye=Eye.OD,
            sphere=-2.50,
            base_curve=8.6,
            diameter=14.2,
        )
        os = ContactLensEye(
            eye=Eye.OS,
            sphere=-2.25,
            base_curve=8.6,
            diameter=14.2,
        )
        rx = ContactLensRx(od=od, os=os)

        assert rx.od.sphere == -2.50
        assert rx.os.sphere == -2.25
        assert not rx.is_toric

    def test_toric_cl_rx(self):
        """Test toric contact lens Rx."""
        od = ContactLensEye(
            eye=Eye.OD,
            sphere=-2.50,
            cylinder=-1.25,
            axis=180,
            base_curve=8.6,
            diameter=14.5,
        )
        rx = ContactLensRx(od=od)

        assert rx.is_toric

    def test_multifocal_cl_rx(self):
        """Test multifocal contact lens Rx."""
        od = ContactLensEye(
            eye=Eye.OD,
            sphere=-1.00,
            add_power=2.00,
            base_curve=8.6,
            diameter=14.2,
        )
        rx = ContactLensRx(od=od)

        assert rx.is_multifocal


class TestGlassesRxModel:
    """Tests for GlassesRx model."""

    def test_create_glasses_rx(self):
        """Test creating glasses Rx."""
        od = GlassesEye(
            eye=Eye.OD,
            sphere=-2.00,
            cylinder=-0.50,
            axis=90,
        )
        os = GlassesEye(
            eye=Eye.OS,
            sphere=-2.25,
            cylinder=-0.75,
            axis=85,
        )
        rx = GlassesRx(od=od, os=os)

        assert rx.od.sphere == -2.00
        assert rx.has_cylinder

    def test_progressive_rx(self):
        """Test progressive glasses Rx."""
        od = GlassesEye(
            eye=Eye.OD,
            sphere=-1.00,
            cylinder=-0.50,
            axis=180,
            add_power=2.00,
        )
        rx = GlassesRx(od=od, rx_type=RxType.PROGRESSIVE)

        assert rx.has_add
        assert rx.is_progressive_candidate

    def test_rx_with_pd(self):
        """Test Rx with PD."""
        rx = GlassesRx(
            od=GlassesEye(eye=Eye.OD, sphere=-1.00),
            os=GlassesEye(eye=Eye.OS, sphere=-1.00),
            pd_distance=64.0,
            pd_near=61.0,
        )

        assert rx.pd_distance == 64.0
        assert rx.pd_near == 61.0
