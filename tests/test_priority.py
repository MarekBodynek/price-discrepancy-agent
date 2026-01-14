"""
Tests for priority merge module.
"""

from datetime import date

from src.core.models import DataSource, ExtractedData
from src.core.priority import PriorityMerger


def test_priority_merge_ocr_wins():
    """Test that OCR data has highest priority."""
    ocr_data = ExtractedData(
        source=DataSource.OCR,
        source_details="OCR",
        supplier_name="Supplier from OCR",
        delivery_date=date(2024, 1, 15),
    )

    attachment_data = ExtractedData(
        source=DataSource.ATTACHMENT,
        source_details="Excel",
        supplier_name="Supplier from Excel",
        delivery_date=date(2024, 1, 20),
    )

    body_data = ExtractedData(
        source=DataSource.BODY,
        source_details="Body",
        supplier_name="Supplier from Body",
        delivery_date=date(2024, 1, 25),
    )

    merger = PriorityMerger()
    merged, conflicts = merger.merge_all([ocr_data, attachment_data, body_data])

    # OCR should win
    assert merged.supplier_name == "Supplier from OCR"
    assert merged.delivery_date == date(2024, 1, 15)
    assert len(conflicts) >= 2  # Should have conflicts for both fields


def test_priority_merge_eans_combined():
    """Test that EANs are combined from all sources."""
    ocr_data = ExtractedData(
        source=DataSource.OCR,
        source_details="OCR",
        eans=["12345678", "11111111"],
    )

    attachment_data = ExtractedData(
        source=DataSource.ATTACHMENT,
        source_details="Excel",
        eans=["87654321", "12345678"],  # Duplicate
    )

    merger = PriorityMerger()
    merged, _ = merger.merge_all([ocr_data, attachment_data])

    # Should have all unique EANs
    assert len(merged.eans) == 3
    assert "12345678" in merged.eans
    assert "11111111" in merged.eans
    assert "87654321" in merged.eans


def test_priority_merge_dict_fields():
    """Test merging of dictionary fields (prices per EAN)."""
    ocr_data = ExtractedData(
        source=DataSource.OCR,
        source_details="OCR",
        supplier_prices={"12345678": 10.50},
    )

    attachment_data = ExtractedData(
        source=DataSource.ATTACHMENT,
        source_details="Excel",
        supplier_prices={"12345678": 15.00, "87654321": 20.00},
    )

    merger = PriorityMerger()
    merged, conflicts = merger.merge_all([ocr_data, attachment_data])

    # OCR price should win for 12345678
    assert merged.supplier_prices["12345678"] == 10.50
    # Attachment price should be present for 87654321
    assert merged.supplier_prices["87654321"] == 20.00
    # Should have conflict for 12345678
    assert any("12345678" in c for c in conflicts)


def test_priority_merge_empty_extractions():
    """Test merging with empty extractions list."""
    merger = PriorityMerger()
    merged, conflicts = merger.merge_all([])

    assert merged.source == DataSource.BODY
    assert merged.eans == []
    assert len(conflicts) == 0
