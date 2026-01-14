"""
Tests for text extraction utilities.
"""

from datetime import date

from src.utils.text import (
    extract_dates,
    extract_eans,
    extract_invoice_numbers,
    extract_prices,
    find_date_by_keyword,
)


def test_extract_eans():
    """Test EAN extraction."""
    text = "Products: 12345678, 1234567890123"
    eans = extract_eans(text)
    assert "12345678" in eans
    assert "1234567890123" in eans


def test_extract_prices():
    """Test price extraction."""
    text = "Price: €10.50, another item costs 25.99 EUR"
    prices = extract_prices(text)
    assert 10.50 in prices
    assert 25.99 in prices


def test_extract_invoice_numbers():
    """Test invoice number extraction."""
    text = "Invoice: INV-2024-001"
    invoices = extract_invoice_numbers(text)
    assert "INV-2024-001" in invoices

    text2 = "Račun #ABC/123"
    invoices2 = extract_invoice_numbers(text2)
    assert "ABC/123" in invoices2


def test_extract_dates():
    """Test date extraction."""
    text = "Date: 2024-01-15"
    dates = extract_dates(text)
    assert date(2024, 1, 15) in dates

    text2 = "Delivered on 15/01/2024"
    dates2 = extract_dates(text2)
    assert date(2024, 1, 15) in dates2

    text3 = "Created 15.01.2024"
    dates3 = extract_dates(text3)
    assert date(2024, 1, 15) in dates3


def test_find_date_by_keyword():
    """Test finding date near keyword."""
    text = "Delivery Date: 2024-01-15"
    delivery_date = find_date_by_keyword(text, "delivery")
    assert delivery_date == date(2024, 1, 15)

    text2 = "Order created on 2024-02-20"
    order_date = find_date_by_keyword(text2, "order")
    assert order_date == date(2024, 2, 20)

    text3 = "No date here"
    no_date = find_date_by_keyword(text3, "delivery")
    assert no_date is None
