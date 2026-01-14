"""
Data normalization utilities.
"""

from datetime import date
from typing import Optional


class Normalizers:
    """Data normalization functions."""

    @staticmethod
    def normalize_ean(ean: str) -> str:
        """
        Normalize EAN code.

        Args:
            ean: Raw EAN string.

        Returns:
            Normalized EAN (digits only, no padding).
        """
        # Remove non-digits
        ean_digits = "".join(c for c in ean if c.isdigit())

        # Return as-is (8 or 13 digits)
        return ean_digits

    @staticmethod
    def normalize_price(price: float) -> float:
        """
        Normalize price value.

        Args:
            price: Raw price.

        Returns:
            Normalized price (rounded to 2 decimals).
        """
        return round(price, 2)

    @staticmethod
    def normalize_date(date_value: Optional[date]) -> Optional[date]:
        """
        Normalize date (already in correct format).

        Args:
            date_value: Date object.

        Returns:
            Same date object (no transformation needed).
        """
        return date_value

    @staticmethod
    def normalize_text(text: Optional[str]) -> Optional[str]:
        """
        Normalize text field (trim, clean whitespace).

        Args:
            text: Raw text.

        Returns:
            Normalized text or None.
        """
        if not text:
            return None

        # Strip whitespace
        normalized = text.strip()

        # Replace multiple spaces with single space
        normalized = " ".join(normalized.split())

        return normalized if normalized else None

    @staticmethod
    def normalize_supplier_name(name: Optional[str]) -> Optional[str]:
        """
        Normalize supplier name.

        Args:
            name: Raw supplier name.

        Returns:
            Normalized supplier name.
        """
        if not name:
            return None

        # Normalize text
        normalized = Normalizers.normalize_text(name)

        # Optionally convert to title case
        if normalized:
            normalized = normalized.title()

        return normalized

    @staticmethod
    def normalize_store(store: Optional[str]) -> Optional[str]:
        """
        Normalize store/unit identifier.

        Args:
            store: Raw store identifier.

        Returns:
            Normalized store identifier (uppercase).
        """
        if not store:
            return None

        normalized = Normalizers.normalize_text(store)

        if normalized:
            normalized = normalized.upper()

        return normalized

    @staticmethod
    def normalize_invoice_number(invoice: Optional[str]) -> Optional[str]:
        """
        Normalize invoice number.

        Args:
            invoice: Raw invoice number.

        Returns:
            Normalized invoice number (uppercase, trimmed).
        """
        if not invoice:
            return None

        normalized = Normalizers.normalize_text(invoice)

        if normalized:
            normalized = normalized.upper()

        return normalized
