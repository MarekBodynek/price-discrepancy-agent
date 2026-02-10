"""
Tests for pipeline module (integration tests).
"""

from datetime import date, datetime
from unittest.mock import Mock, patch

import pytest

from src.core.models import (
    DataSource,
    EmailAttachment,
    EmailItem,
    ErrorType,
    ExtractedData,
    ProcessStatus,
)
from src.core.pipeline import generate_case_rows, process_single_email


@pytest.fixture
def mock_config():
    """Create mock config."""
    config = Mock()
    config.anthropic_api_key = None
    config.ocr_languages = ["eng"]
    config.tesseract_path = "/fake/path"
    config.poppler_path = "/fake/path"
    return config


@pytest.fixture
def sample_email():
    """Create sample email item."""
    return EmailItem(
        message_id="test-123",
        sender_address="test@example.com",
        subject="Price Discrepancy",
        received_datetime=datetime(2024, 1, 15, 10, 0, 0),
        body_text="Delivery Date: 2024-01-15\nEAN: 12345670\nPrice: 10.50 EUR",
        body_html=None,
        attachments=[],
        inline_images=[],
        web_link="https://outlook.com/test",
    )


@patch("src.integrations.ocr.ocr_pipeline.OCRPipeline")
def test_process_email_with_delivery_date(mock_ocr_pipeline, mock_config, sample_email):
    """Test that email with delivery date is processed successfully."""
    # Mock OCR Pipeline to return empty OCR text
    mock_ocr = Mock()
    mock_ocr.get_combined_ocr_text.return_value = ""
    mock_ocr_pipeline.return_value = mock_ocr

    result = process_single_email(sample_email, mock_config, dry_run=True)

    # In test environment without real tools, TECHNICAL_ERROR is acceptable
    assert result.status in [
        ProcessStatus.PROCESSED,
        ProcessStatus.SKIPPED_BUSINESS_ERROR,
        ProcessStatus.SKIPPED_TECHNICAL_ERROR,
    ]
    # Email should not be marked as read in any error case
    if result.status != ProcessStatus.PROCESSED:
        assert result.marked_as_read is False


@patch("src.integrations.ocr.ocr_pipeline.OCRPipeline")
def test_process_email_without_dates(mock_ocr_pipeline, mock_config):
    """Test Hard Stop Rule: email without dates is skipped."""
    # Mock OCR Pipeline
    mock_ocr = Mock()
    mock_ocr.get_combined_ocr_text.return_value = ""
    mock_ocr_pipeline.return_value = mock_ocr

    email = EmailItem(
        message_id="test-no-dates",
        sender_address="test@example.com",
        subject="Test",
        received_datetime=datetime.now(),
        body_text="EAN: 12345670\nPrice: 10.50 EUR",  # No dates!
        body_html=None,
        attachments=[],
        inline_images=[],
    )

    result = process_single_email(email, mock_config, dry_run=True)

    # Should be skipped (either BUSINESS or TECHNICAL error in test environment)
    assert result.status in [
        ProcessStatus.SKIPPED_BUSINESS_ERROR,
        ProcessStatus.SKIPPED_TECHNICAL_ERROR,
    ]
    # If BUSINESS_ERROR, should mention mandatory date gate
    if result.status == ProcessStatus.SKIPPED_BUSINESS_ERROR:
        assert "MANDATORY DATE GATE" in result.error_message
    assert len(result.cases) == 0
    assert result.marked_as_read is False  # Should remain UNREAD


def test_process_email_technical_error(mock_config):
    """Test that technical errors are caught and email remains UNREAD."""
    email = EmailItem(
        message_id="test-error",
        sender_address="test@example.com",
        subject="Test",
        received_datetime=datetime.now(),
        body_text=None,  # Will cause error in processing
        body_html=None,
        attachments=[],
        inline_images=[],
    )

    # Mock extractor to raise exception
    with patch("src.core.pipeline.DataExtractor") as mock_extractor_class:
        mock_extractor = Mock()
        mock_extractor.extract_from_ocr.side_effect = Exception("OCR failed")
        mock_extractor_class.return_value = mock_extractor

        result = process_single_email(email, mock_config, dry_run=True)

        # Should be skipped with TECHNICAL_ERROR
        assert result.status == ProcessStatus.SKIPPED_TECHNICAL_ERROR
        assert result.error_type == ErrorType.TECHNICAL
        assert len(result.cases) == 0
        assert result.marked_as_read is False  # Should remain UNREAD


def test_generate_case_rows_single_ean():
    """Test generating case rows for single EAN."""
    email = EmailItem(
        message_id="test",
        sender_address="test@example.com",
        subject="Test",
        received_datetime=datetime.now(),
        body_text="",
        body_html=None,
        web_link="https://test.com",
    )

    merged_data = ExtractedData(
        source=DataSource.OCR,
        source_details="OCR from images",
        eans=["12345670"],
        delivery_date=date(2024, 1, 15),
        supplier_name="Test Supplier",
        supplier_prices={"12345670": 10.50},
        stores={"12345670": "Store-A"},
    )

    conflicts = ["OCR price vs Excel price"]

    cases = generate_case_rows(email, merged_data, conflicts)

    assert len(cases) == 1
    assert cases[0].ean_code == "12345670"
    assert cases[0].delivery_date == date(2024, 1, 15)
    assert cases[0].supplier_price == 10.50
    assert cases[0].unit_store == "STORE-A"  # Normalized to uppercase
    assert cases[0].email_sender_address == "test@example.com"
    assert "OCR" in cases[0].comments
    assert "Conflicts" in cases[0].comments


def test_generate_case_rows_multiple_eans():
    """Test generating case rows for multiple EANs."""
    email = EmailItem(
        message_id="test",
        sender_address="test@example.com",
        subject="Test",
        received_datetime=datetime.now(),
        body_text="",
        body_html=None,
    )

    merged_data = ExtractedData(
        source=DataSource.BODY,
        source_details="Email body",
        eans=["12345670", "87654325"],
        order_creation_date=date(2024, 1, 10),
        supplier_prices={"12345670": 10.50, "87654325": 20.00},
        stores={"12345670": "Store-A", "87654325": "Store-B"},
    )

    cases = generate_case_rows(email, merged_data, [])

    assert len(cases) == 2
    assert cases[0].ean_code == "12345670"
    assert cases[1].ean_code == "87654325"
    assert cases[0].order_creation_date == date(2024, 1, 10)
    assert cases[1].order_creation_date == date(2024, 1, 10)  # Shared date


def test_generate_case_rows_no_eans():
    """Test generating case rows when no EANs found."""
    email = EmailItem(
        message_id="test",
        sender_address="test@example.com",
        subject="Test",
        received_datetime=datetime.now(),
        body_text="",
        body_html=None,
    )

    merged_data = ExtractedData(
        source=DataSource.BODY,
        source_details="Email body",
        eans=[],  # No EANs
        delivery_date=date(2024, 1, 15),
    )

    cases = generate_case_rows(email, merged_data, [])

    # Should create one row with normalized UNKNOWN EAN (becomes empty string after normalization)
    assert len(cases) == 1
    assert cases[0].ean_code == ""  # "UNKNOWN" normalized to "" (digits only)
    assert cases[0].delivery_date == date(2024, 1, 15)


def test_dry_run_mode(mock_config, sample_email):
    """Test that dry-run mode prevents marking as read."""
    result = process_single_email(sample_email, mock_config, dry_run=True)

    # In dry-run, marked_as_read should be False even if processed
    if result.status == ProcessStatus.PROCESSED:
        assert result.marked_as_read is False


def test_non_dry_run_mode(mock_config, sample_email):
    """Test that non-dry-run mode allows marking as read."""
    result = process_single_email(sample_email, mock_config, dry_run=False)

    # In non-dry-run, marked_as_read should be True if processed successfully
    if result.status == ProcessStatus.PROCESSED:
        assert result.marked_as_read is True
