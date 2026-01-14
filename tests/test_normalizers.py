"""
Tests for normalizers module.
"""

from src.core.normalize import Normalizers


def test_normalize_ean():
    """Test EAN normalization."""
    assert Normalizers.normalize_ean("12345678") == "12345678"
    assert Normalizers.normalize_ean("1234 5678") == "12345678"
    assert Normalizers.normalize_ean("EAN: 12345678") == "12345678"


def test_normalize_price():
    """Test price normalization."""
    assert Normalizers.normalize_price(10.5) == 10.50
    assert Normalizers.normalize_price(10.123) == 10.12
    assert Normalizers.normalize_price(10.999) == 11.00


def test_normalize_text():
    """Test text normalization."""
    assert Normalizers.normalize_text("  hello  world  ") == "hello world"
    assert Normalizers.normalize_text("hello\n\nworld") == "hello world"
    assert Normalizers.normalize_text("") is None
    assert Normalizers.normalize_text("   ") is None
    assert Normalizers.normalize_text(None) is None


def test_normalize_supplier_name():
    """Test supplier name normalization."""
    assert Normalizers.normalize_supplier_name("acme corp") == "Acme Corp"
    assert Normalizers.normalize_supplier_name("  ACME  CORP  ") == "Acme Corp"
    assert Normalizers.normalize_supplier_name(None) is None


def test_normalize_store():
    """Test store identifier normalization."""
    assert Normalizers.normalize_store("store-123") == "STORE-123"
    assert Normalizers.normalize_store("  unit a  ") == "UNIT A"
    assert Normalizers.normalize_store(None) is None


def test_normalize_invoice_number():
    """Test invoice number normalization."""
    assert Normalizers.normalize_invoice_number("inv-123") == "INV-123"
    assert Normalizers.normalize_invoice_number("  abc/456  ") == "ABC/456"
    assert Normalizers.normalize_invoice_number(None) is None
