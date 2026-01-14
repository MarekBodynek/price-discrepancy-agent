"""
Tests for validators module.
"""

from datetime import date

import pytest

from src.core.models import DataSource, ExtractedData
from src.core.validators import ValidationError, Validators


def test_mandatory_date_gate_with_delivery_date():
    """Test that delivery date alone passes the gate."""
    extracted = ExtractedData(
        source=DataSource.BODY,
        source_details="test",
        delivery_date=date(2024, 1, 15),
    )

    # Should not raise
    Validators.validate_mandatory_date_gate(extracted)


def test_mandatory_date_gate_with_order_date():
    """Test that order creation date alone passes the gate."""
    extracted = ExtractedData(
        source=DataSource.BODY,
        source_details="test",
        order_creation_date=date(2024, 1, 15),
    )

    # Should not raise
    Validators.validate_mandatory_date_gate(extracted)


def test_mandatory_date_gate_with_both_dates():
    """Test that both dates pass the gate."""
    extracted = ExtractedData(
        source=DataSource.BODY,
        source_details="test",
        delivery_date=date(2024, 1, 15),
        order_creation_date=date(2024, 1, 10),
    )

    # Should not raise
    Validators.validate_mandatory_date_gate(extracted)


def test_mandatory_date_gate_fails_without_dates():
    """Test that missing both dates fails the gate (HARD STOP)."""
    extracted = ExtractedData(
        source=DataSource.BODY,
        source_details="test",
    )

    # Should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        Validators.validate_mandatory_date_gate(extracted)

    assert "MANDATORY DATE GATE" in str(exc_info.value)


def test_validate_ean():
    """Test EAN validation."""
    assert Validators.validate_ean("12345678") is True  # 8 digits
    assert Validators.validate_ean("1234567890123") is True  # 13 digits
    assert Validators.validate_ean("123") is False  # Too short
    assert Validators.validate_ean("12345678901234") is False  # Too long
    assert Validators.validate_ean("1234abcd") is False  # Non-digits


def test_validate_price():
    """Test price validation."""
    assert Validators.validate_price(10.50) is True
    assert Validators.validate_price(0.01) is True
    assert Validators.validate_price(0.0) is False
    assert Validators.validate_price(-5.0) is False


def test_validate_date_range():
    """Test date range validation."""
    assert Validators.validate_date_range(date(2024, 1, 15)) is True
    assert Validators.validate_date_range(date(1999, 1, 1)) is False  # Before 2000
    assert Validators.validate_date_range(date(2101, 1, 1)) is False  # After 2100
    assert Validators.validate_date_range(None) is False
