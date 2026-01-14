"""
Data extractors from various sources.
"""

from typing import Optional

from src.config import Config
from src.core.models import DataSource, EmailAttachment, EmailItem, ExtractedData
from src.integrations.excel.parser import ExcelParser
from src.integrations.ocr.ocr_pipeline import OCRPipeline
from src.utils.text import (
    extract_dates,
    extract_eans,
    extract_invoice_numbers,
    extract_prices,
    extract_stores,
    extract_suppliers,
    find_date_by_keyword,
)


class DataExtractor:
    """Extracts structured data from email sources."""

    def __init__(self, config: Config):
        """
        Initialize extractor.

        Args:
            config: Application configuration.
        """
        self.config = config
        self.ocr_pipeline = OCRPipeline(config)
        self.excel_parser = ExcelParser()

    def extract_from_ocr(self, email: EmailItem) -> Optional[ExtractedData]:
        """
        Extract data from OCR (images).

        Args:
            email: Email item.

        Returns:
            ExtractedData or None if no images.
        """
        # Get combined OCR text
        ocr_text = self.ocr_pipeline.get_combined_ocr_text(email)

        if not ocr_text:
            return None

        # Extract fields from OCR text
        extracted = ExtractedData(
            source=DataSource.OCR,
            source_details="OCR from images",
            eans=extract_eans(ocr_text),
        )

        # Extract dates
        extracted.delivery_date = find_date_by_keyword(ocr_text, "delivery")
        extracted.order_creation_date = find_date_by_keyword(ocr_text, "order")
        extracted.document_creation_date = find_date_by_keyword(ocr_text, "document|created|date")

        # Extract supplier info
        suppliers = extract_suppliers(ocr_text)
        extracted.supplier_name = suppliers[0] if suppliers else None

        invoices = extract_invoice_numbers(ocr_text)
        extracted.supplier_invoice_number = invoices[0] if invoices else None

        # Extract prices (match to EANs if possible)
        prices = extract_prices(ocr_text)
        # Simple heuristic: assign first N prices to first N EANs
        for i, ean in enumerate(extracted.eans):
            if i < len(prices):
                extracted.supplier_prices[ean] = prices[i]

        # Extract stores
        stores = extract_stores(ocr_text)
        for i, ean in enumerate(extracted.eans):
            if i < len(stores):
                extracted.stores[ean] = stores[i]

        return extracted

    def extract_from_attachments(self, email: EmailItem) -> list[ExtractedData]:
        """
        Extract data from attachments (Excel, PDF).

        Args:
            email: Email item.

        Returns:
            List of ExtractedData (one per attachment).
        """
        extractions = []

        for att in email.attachments:
            # Skip images (handled by OCR)
            if att.content_type.startswith("image/"):
                continue

            extracted = None

            # Excel files
            if att.content_type in (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel",
            ) or att.filename.lower().endswith((".xlsx", ".xls")):
                extracted = self._extract_from_excel(att)

            # PDF files (text extraction)
            elif att.content_type == "application/pdf" or att.filename.lower().endswith(".pdf"):
                extracted = self._extract_from_pdf_text(att)

            if extracted:
                extractions.append(extracted)

        return extractions

    def _extract_from_excel(self, attachment: EmailAttachment) -> Optional[ExtractedData]:
        """Extract data from Excel attachment."""
        try:
            text = self.excel_parser.extract_text_from_xlsx(attachment.content)
        except Exception:
            return None

        extracted = ExtractedData(
            source=DataSource.ATTACHMENT,
            source_details=f"Attachment: {attachment.filename}",
            eans=extract_eans(text),
        )

        # Extract dates
        extracted.delivery_date = find_date_by_keyword(text, "delivery")
        extracted.order_creation_date = find_date_by_keyword(text, "order")
        extracted.document_creation_date = find_date_by_keyword(text, "document|created|date")

        # Extract supplier info
        suppliers = extract_suppliers(text)
        extracted.supplier_name = suppliers[0] if suppliers else None

        invoices = extract_invoice_numbers(text)
        extracted.supplier_invoice_number = invoices[0] if invoices else None

        # Extract prices
        prices = extract_prices(text)
        for i, ean in enumerate(extracted.eans):
            if i < len(prices):
                extracted.supplier_prices[ean] = prices[i]

        # Extract stores
        stores = extract_stores(text)
        for i, ean in enumerate(extracted.eans):
            if i < len(stores):
                extracted.stores[ean] = stores[i]

        return extracted

    def _extract_from_pdf_text(self, attachment: EmailAttachment) -> Optional[ExtractedData]:
        """Extract data from PDF text (not OCR)."""
        # For now, use simple text extraction
        # TODO: Use pdfplumber for better extraction
        try:
            import pdfplumber
            import io

            with pdfplumber.open(io.BytesIO(attachment.content)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except Exception:
            return None

        if not text:
            return None

        extracted = ExtractedData(
            source=DataSource.ATTACHMENT,
            source_details=f"Attachment: {attachment.filename}",
            eans=extract_eans(text),
        )

        # Extract dates
        extracted.delivery_date = find_date_by_keyword(text, "delivery")
        extracted.order_creation_date = find_date_by_keyword(text, "order")
        extracted.document_creation_date = find_date_by_keyword(text, "document|created|date")

        # Extract supplier info
        suppliers = extract_suppliers(text)
        extracted.supplier_name = suppliers[0] if suppliers else None

        invoices = extract_invoice_numbers(text)
        extracted.supplier_invoice_number = invoices[0] if invoices else None

        # Extract prices
        prices = extract_prices(text)
        for i, ean in enumerate(extracted.eans):
            if i < len(prices):
                extracted.supplier_prices[ean] = prices[i]

        # Extract stores
        stores = extract_stores(text)
        for i, ean in enumerate(extracted.eans):
            if i < len(stores):
                extracted.stores[ean] = stores[i]

        return extracted

    def extract_from_body(self, email: EmailItem) -> Optional[ExtractedData]:
        """
        Extract data from email body.

        Args:
            email: Email item.

        Returns:
            ExtractedData or None.
        """
        # Use text body if available, otherwise strip HTML
        body_text = email.body_text or email.body_html or ""

        if not body_text:
            return None

        # Simple HTML stripping (remove tags)
        if email.body_html and not email.body_text:
            import re
            body_text = re.sub(r'<[^>]+>', ' ', body_text)

        extracted = ExtractedData(
            source=DataSource.BODY,
            source_details="Email body",
            eans=extract_eans(body_text),
        )

        # Extract dates
        extracted.delivery_date = find_date_by_keyword(body_text, "delivery")
        extracted.order_creation_date = find_date_by_keyword(body_text, "order")
        extracted.document_creation_date = find_date_by_keyword(body_text, "document|created|date")

        # Extract supplier info
        suppliers = extract_suppliers(body_text)
        extracted.supplier_name = suppliers[0] if suppliers else None

        invoices = extract_invoice_numbers(body_text)
        extracted.supplier_invoice_number = invoices[0] if invoices else None

        # Extract prices
        prices = extract_prices(body_text)
        for i, ean in enumerate(extracted.eans):
            if i < len(prices):
                extracted.supplier_prices[ean] = prices[i]

        # Extract stores
        stores = extract_stores(body_text)
        for i, ean in enumerate(extracted.eans):
            if i < len(stores):
                extracted.stores[ean] = stores[i]

        return extracted
