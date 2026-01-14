"""
Tests for extractors module.
"""

from datetime import date, datetime
from unittest.mock import Mock, patch

import pytest

from src.core.extractors import DataExtractor
from src.core.models import DataSource, EmailAttachment, EmailItem


@pytest.fixture
def mock_config():
    """Create mock config."""
    config = Mock()
    config.ocr_languages = ["eng"]
    config.tesseract_path = "/fake/path"
    config.poppler_path = "/fake/path"
    return config


@patch("src.core.extractors.OCRPipeline")
def test_extract_from_body_with_ean(mock_ocr_pipeline, mock_config):
    """Test extracting EAN from email body."""
    # Mock OCR Pipeline
    mock_ocr = Mock()
    mock_ocr.get_combined_ocr_text.return_value = ""
    mock_ocr_pipeline.return_value = mock_ocr

    email = EmailItem(
        message_id="test",
        sender_address="test@example.com",
        subject="Test",
        received_datetime=datetime.now(),
        body_text="Product EAN: 12345678\nPrice: 10.50 EUR",
        body_html=None,
    )

    extractor = DataExtractor(mock_config)
    result = extractor.extract_from_body(email)

    assert result is not None
    assert result.source == DataSource.BODY
    assert "12345678" in result.eans


@patch("src.core.extractors.OCRPipeline")
def test_extract_from_body_with_dates(mock_ocr_pipeline, mock_config):
    """Test extracting dates from email body."""
    # Mock OCR Pipeline
    mock_ocr = Mock()
    mock_ocr.get_combined_ocr_text.return_value = ""
    mock_ocr_pipeline.return_value = mock_ocr

    email = EmailItem(
        message_id="test",
        sender_address="test@example.com",
        subject="Test",
        received_datetime=datetime.now(),
        body_text="Delivery Date: 2024-01-15\nOrder created on 2024-01-10",
        body_html=None,
    )

    extractor = DataExtractor(mock_config)
    result = extractor.extract_from_body(email)

    assert result is not None
    assert result.delivery_date == date(2024, 1, 15)
    assert result.order_creation_date == date(2024, 1, 10)


@patch("src.core.extractors.OCRPipeline")
def test_extract_from_body_with_prices(mock_ocr_pipeline, mock_config):
    """Test extracting prices from email body."""
    # Mock OCR Pipeline
    mock_ocr = Mock()
    mock_ocr.get_combined_ocr_text.return_value = ""
    mock_ocr_pipeline.return_value = mock_ocr

    email = EmailItem(
        message_id="test",
        sender_address="test@example.com",
        subject="Test",
        received_datetime=datetime.now(),
        body_text="EAN 12345678 Price: 10.50 EUR\nEAN 87654321 Price: 20.00 EUR",
        body_html=None,
    )

    extractor = DataExtractor(mock_config)
    result = extractor.extract_from_body(email)

    assert result is not None
    assert len(result.eans) >= 1  # At least one EAN found


@patch("src.core.extractors.OCRPipeline")
def test_extract_from_body_empty(mock_ocr_pipeline, mock_config):
    """Test extracting from empty body."""
    # Mock OCR Pipeline
    mock_ocr = Mock()
    mock_ocr.get_combined_ocr_text.return_value = ""
    mock_ocr_pipeline.return_value = mock_ocr

    email = EmailItem(
        message_id="test",
        sender_address="test@example.com",
        subject="Test",
        received_datetime=datetime.now(),
        body_text="",
        body_html=None,
    )

    extractor = DataExtractor(mock_config)
    result = extractor.extract_from_body(email)

    # Should return None for empty body
    assert result is None


@patch("src.core.extractors.OCRPipeline")
def test_extract_from_body_html_stripping(mock_ocr_pipeline, mock_config):
    """Test that HTML is stripped from body."""
    # Mock OCR Pipeline
    mock_ocr = Mock()
    mock_ocr.get_combined_ocr_text.return_value = ""
    mock_ocr_pipeline.return_value = mock_ocr

    email = EmailItem(
        message_id="test",
        sender_address="test@example.com",
        subject="Test",
        received_datetime=datetime.now(),
        body_text=None,
        body_html="<p>EAN: <b>12345678</b></p><p>Delivery: 2024-01-15</p>",
    )

    extractor = DataExtractor(mock_config)
    result = extractor.extract_from_body(email)

    assert result is not None
    # HTML should be stripped, EAN should still be found
    assert "12345678" in result.eans


@patch("src.core.extractors.OCRPipeline")
@patch("src.core.extractors.ExcelParser")
def test_extract_from_excel_attachment(mock_parser_class, mock_ocr_pipeline, mock_config):
    """Test extracting from Excel attachment."""
    # Mock OCR Pipeline
    mock_ocr = Mock()
    mock_ocr.get_combined_ocr_text.return_value = ""
    mock_ocr_pipeline.return_value = mock_ocr

    # Mock ExcelParser
    mock_parser = Mock()
    mock_parser.extract_text_from_xlsx.return_value = "EAN: 12345678\nDelivery Date: 2024-01-15"
    mock_parser_class.return_value = mock_parser

    email = EmailItem(
        message_id="test",
        sender_address="test@example.com",
        subject="Test",
        received_datetime=datetime.now(),
        body_text="",
        body_html=None,
        attachments=[
            EmailAttachment(
                filename="report.xlsx",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                content=b"fake-excel-data",
                size=100,
            )
        ],
    )

    extractor = DataExtractor(mock_config)
    results = extractor.extract_from_attachments(email)

    assert len(results) >= 1
    assert results[0].source == DataSource.ATTACHMENT
    assert "12345678" in results[0].eans
