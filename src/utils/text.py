"""
Text extraction utilities with regex patterns.
"""

import re
from datetime import date, datetime
from typing import Optional


# EAN patterns (8 or 13 digits)
EAN_PATTERN = re.compile(r'\b(\d{8}|\d{13})\b')

# Price patterns (decimal numbers with optional currency)
PRICE_PATTERN = re.compile(r'(?:€|EUR|USD|\$)?\s*(\d+[.,]\d{2})\s*(?:€|EUR|USD|\$)?', re.IGNORECASE)

# Invoice number patterns
INVOICE_PATTERN = re.compile(r'(?:invoice|račun|faktura|inv\.?)\s*:?\s*#?\s*([A-Z0-9\-/]+)', re.IGNORECASE)

# Date patterns (various formats)
DATE_PATTERNS = [
    # YYYY-MM-DD or YYYY/MM/DD
    (re.compile(r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b'), '%Y-%m-%d'),
    # DD-MM-YYYY or DD/MM/YYYY or DD.MM.YYYY
    (re.compile(r'\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b'), '%d-%m-%Y'),
    # DD MMM YYYY (e.g., 15 Jan 2024)
    (re.compile(r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\b', re.IGNORECASE), '%d %b %Y'),
]

# Store/Unit patterns
STORE_PATTERN = re.compile(r'(?:store|unit|enota|trgovina)\s*:?\s*([A-Z0-9\-]+)', re.IGNORECASE)

# Supplier patterns
SUPPLIER_PATTERN = re.compile(r'(?:supplier|dobavitelj|prodajalec)\s*:?\s*([A-Za-z0-9\s\-\.]+?)(?:\n|$)', re.IGNORECASE)


def extract_eans(text: str) -> list[str]:
    """
    Extract EAN codes from text.

    Args:
        text: Input text.

    Returns:
        List of unique EAN codes.
    """
    matches = EAN_PATTERN.findall(text)
    return list(set(matches))


def extract_prices(text: str) -> list[float]:
    """
    Extract prices from text.

    Args:
        text: Input text.

    Returns:
        List of prices as floats.
    """
    matches = PRICE_PATTERN.findall(text)
    prices = []

    for match in matches:
        # Replace comma with dot for parsing
        price_str = match.replace(',', '.')
        try:
            price = float(price_str)
            prices.append(price)
        except ValueError:
            pass

    return prices


def extract_invoice_numbers(text: str) -> list[str]:
    """
    Extract invoice numbers from text.

    Args:
        text: Input text.

    Returns:
        List of invoice numbers.
    """
    matches = INVOICE_PATTERN.findall(text)
    return [m.strip() for m in matches]


def extract_dates(text: str) -> list[date]:
    """
    Extract dates from text.

    Args:
        text: Input text.

    Returns:
        List of date objects.
    """
    dates_found = []

    for pattern, date_format in DATE_PATTERNS:
        matches = pattern.findall(text)

        for match in matches:
            if isinstance(match, tuple):
                # Reconstruct date string
                if date_format == '%Y-%m-%d':
                    date_str = f"{match[0]}-{match[1]}-{match[2]}"
                elif date_format == '%d-%m-%Y':
                    date_str = f"{match[0]}-{match[1]}-{match[2]}"
                elif date_format == '%d %b %Y':
                    date_str = f"{match[0]} {match[1]} {match[2]}"
            else:
                date_str = match

            try:
                parsed_date = datetime.strptime(date_str, date_format).date()
                dates_found.append(parsed_date)
            except ValueError:
                pass

    return dates_found


def extract_stores(text: str) -> list[str]:
    """
    Extract store/unit identifiers from text.

    Args:
        text: Input text.

    Returns:
        List of store identifiers.
    """
    matches = STORE_PATTERN.findall(text)
    return [m.strip() for m in matches]


def extract_suppliers(text: str) -> list[str]:
    """
    Extract supplier names from text.

    Args:
        text: Input text.

    Returns:
        List of supplier names.
    """
    matches = SUPPLIER_PATTERN.findall(text)
    return [m.strip() for m in matches]


def find_date_by_keyword(text: str, keyword: str) -> Optional[date]:
    """
    Find date near a specific keyword.

    Args:
        text: Input text.
        keyword: Keyword to search for (e.g., "delivery", "order").

    Returns:
        Date object or None.
    """
    # Search for keyword
    keyword_pattern = re.compile(rf'{keyword}\s*:?\s*', re.IGNORECASE)
    match = keyword_pattern.search(text)

    if not match:
        return None

    # Extract text after keyword (next 50 characters)
    start_pos = match.end()
    snippet = text[start_pos:start_pos + 50]

    # Try to find date in snippet
    dates = extract_dates(snippet)

    return dates[0] if dates else None
