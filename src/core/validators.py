"""
Data validation - mandatory date gate and other checks.
"""

from datetime import date
from typing import Optional

from src.core.models import ExtractedData


class ValidationError(Exception):
    """Validation error (business rule violation)."""
    pass


class Validators:
    """Data validators."""

    @staticmethod
    def validate_mandatory_date_gate(extracted: ExtractedData) -> None:
        """
        Validate mandatory date gate (HARD STOP RULE).

        Email MUST contain at least one of:
        - Delivery Date
        - Order Creation Date

        Args:
            extracted: Extracted data to validate.

        Raises:
            ValidationError: If neither date is present.
        """
        has_delivery = extracted.delivery_date is not None
        has_order = extracted.order_creation_date is not None

        if not has_delivery and not has_order:
            raise ValidationError(
                "MANDATORY DATE GATE: Email must contain at least one of "
                "Delivery Date or Order Creation Date. Neither was found."
            )

    @staticmethod
    def validate_ean(ean: str) -> bool:
        """
        Validate EAN code format.

        Args:
            ean: EAN code string.

        Returns:
            True if valid, False otherwise.
        """
        # EAN must be 8 or 13 digits
        if not ean.isdigit():
            return False

        if len(ean) not in (8, 13):
            return False

        return True

    @staticmethod
    def validate_price(price: float) -> bool:
        """
        Validate price value.

        Args:
            price: Price value.

        Returns:
            True if valid, False otherwise.
        """
        # Price must be positive
        return price > 0

    @staticmethod
    def validate_date_range(
        date_value: Optional[date],
        min_year: int = 2000,
        max_year: int = 2100,
    ) -> bool:
        """
        Validate date is in reasonable range.

        Args:
            date_value: Date to validate.
            min_year: Minimum year.
            max_year: Maximum year.

        Returns:
            True if valid, False if invalid or None.
        """
        if date_value is None:
            return False

        return min_year <= date_value.year <= max_year

    @staticmethod
    def validate_extracted_data(extracted: ExtractedData) -> list[str]:
        """
        Validate extracted data and return list of warnings.

        Args:
            extracted: Extracted data.

        Returns:
            List of warning messages (empty if all valid).
        """
        warnings = []

        # Validate EANs
        for ean in extracted.eans:
            if not Validators.validate_ean(ean):
                warnings.append(f"Invalid EAN format: {ean}")

        # Validate dates
        for date_field, date_value in [
            ("delivery_date", extracted.delivery_date),
            ("order_creation_date", extracted.order_creation_date),
            ("document_creation_date", extracted.document_creation_date),
        ]:
            if date_value and not Validators.validate_date_range(date_value):
                warnings.append(f"Date out of range: {date_field} = {date_value}")

        # Validate prices
        for ean, price in extracted.supplier_prices.items():
            if not Validators.validate_price(price):
                warnings.append(f"Invalid supplier price for EAN {ean}: {price}")

        for ean, price in extracted.internal_prices.items():
            if not Validators.validate_price(price):
                warnings.append(f"Invalid internal price for EAN {ean}: {price}")

        return warnings
