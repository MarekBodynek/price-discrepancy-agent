"""
Data extractors from various sources.
"""

from typing import Optional

from src.config import Config
from src.core.excel_structured_extractor import extract_structured_from_excel
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
    is_valid_ean,
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

        # Initialize Claude client if API key is available (used as smart fallback)
        self.claude_client = None
        if config.anthropic_api_key:
            try:
                from src.integrations.anthropic.client import ClaudeClient
                self.claude_client = ClaudeClient(config)
            except Exception:
                pass

    def extract_from_ocr(self, email: EmailItem) -> Optional[ExtractedData]:
        """
        Extract data from OCR (images).

        Strategy:
        1. Get OCR text from images
        2. Try regex-based extraction first
        3. If Claude client available and regex found few EANs, use Claude as smart fallback
        4. Merge results (Claude enriches regex)

        Args:
            email: Email item.

        Returns:
            ExtractedData or None if no images.
        """
        # Get combined OCR text
        ocr_text = self.ocr_pipeline.get_combined_ocr_text(email)

        if not ocr_text:
            return None

        # 1. Regex-based extraction
        extracted = ExtractedData(
            source=DataSource.OCR,
            source_details="OCR from images",
            eans=extract_eans(ocr_text),
        )

        extracted.delivery_date = find_date_by_keyword(ocr_text, "delivery")
        extracted.order_creation_date = find_date_by_keyword(ocr_text, "order")
        extracted.document_creation_date = find_date_by_keyword(ocr_text, "document|created|date")

        suppliers = extract_suppliers(ocr_text)
        extracted.supplier_name = suppliers[0] if suppliers else None

        invoices = extract_invoice_numbers(ocr_text)
        extracted.supplier_invoice_number = invoices[0] if invoices else None

        prices = extract_prices(ocr_text)
        for i, ean in enumerate(extracted.eans):
            if i < len(prices):
                extracted.supplier_prices[ean] = prices[i]

        stores = extract_stores(ocr_text)
        for i, ean in enumerate(extracted.eans):
            if i < len(stores):
                extracted.stores[ean] = stores[i]

        # 2. Claude smart fallback: if regex found few results, ask Claude
        if self.claude_client and len(extracted.eans) == 0:
            claude_data = self._claude_extract_structured(ocr_text)
            if claude_data:
                extracted = self._merge_claude_into_extracted(extracted, claude_data)

        return extracted

    def _claude_extract_structured(self, text: str) -> Optional[dict]:
        """Call Claude extract_structured_data, returning parsed dict or None."""
        if not self.claude_client:
            return None
        try:
            return self.claude_client.extract_structured_data(text)
        except Exception:
            return None

    def _merge_claude_into_extracted(
        self, extracted: ExtractedData, claude_data: dict
    ) -> ExtractedData:
        """Merge Claude structured extraction results into an ExtractedData object.

        Claude data only fills gaps — it does not overwrite existing regex results.
        """
        from datetime import date as _date

        # EANs
        claude_eans = claude_data.get("ean_codes") or []
        for ean in claude_eans:
            ean_str = str(ean).strip()
            if is_valid_ean(ean_str) and ean_str not in extracted.eans:
                extracted.eans.append(ean_str)

        # Dates
        for field, key in [
            ("delivery_date", "delivery_date"),
            ("order_creation_date", "order_creation_date"),
            ("document_creation_date", "document_creation_date"),
        ]:
            if getattr(extracted, field) is None and claude_data.get(key):
                try:
                    val = claude_data[key]
                    if isinstance(val, str):
                        setattr(extracted, field, _date.fromisoformat(val))
                except (ValueError, TypeError):
                    pass

        # Supplier info
        if not extracted.supplier_name and claude_data.get("supplier_name"):
            extracted.supplier_name = claude_data["supplier_name"]
        if not extracted.supplier_invoice_number and claude_data.get("supplier_invoice_number"):
            extracted.supplier_invoice_number = claude_data["supplier_invoice_number"]

        # Prices
        for ean, price in (claude_data.get("supplier_prices") or {}).items():
            if ean not in extracted.supplier_prices:
                try:
                    extracted.supplier_prices[ean] = float(price)
                except (ValueError, TypeError):
                    pass

        for ean, price in (claude_data.get("internal_prices") or {}).items():
            if ean not in extracted.internal_prices:
                try:
                    extracted.internal_prices[ean] = float(price)
                except (ValueError, TypeError):
                    pass

        # Stores
        for ean, store in (claude_data.get("stores") or {}).items():
            if ean not in extracted.stores:
                extracted.stores[ean] = str(store)

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
        """Extract data from Excel attachment.

        Strategy:
        1. Try structured extraction (header-based, row-level association)
        2. If structured returns data, enrich missing dates/supplier from plain text
        3. If structured returns None, fallback to plain-text method
        """
        # 1. Try structured extraction first
        structured = extract_structured_from_excel(attachment.content, attachment.filename)

        if structured and structured.eans:
            # Enrich with dates/supplier from plain text if structured missed them
            try:
                text = self.excel_parser.extract_text_from_xlsx(attachment.content)
            except Exception:
                text = ""

            if text:
                if not structured.delivery_date:
                    structured.delivery_date = find_date_by_keyword(text, "delivery")
                if not structured.order_creation_date:
                    structured.order_creation_date = find_date_by_keyword(text, "order")
                if not structured.document_creation_date:
                    structured.document_creation_date = find_date_by_keyword(text, "document|created|date")
                if not structured.supplier_name:
                    suppliers = extract_suppliers(text)
                    structured.supplier_name = suppliers[0] if suppliers else None
                if not structured.supplier_invoice_number:
                    invoices = extract_invoice_numbers(text)
                    structured.supplier_invoice_number = invoices[0] if invoices else None

            return structured

        # 2. Fallback: plain-text extraction
        try:
            text = self.excel_parser.extract_text_from_xlsx(attachment.content)
        except Exception:
            return None

        extracted = ExtractedData(
            source=DataSource.ATTACHMENT,
            source_details=f"Attachment: {attachment.filename}",
            eans=extract_eans(text),
        )

        extracted.delivery_date = find_date_by_keyword(text, "delivery")
        extracted.order_creation_date = find_date_by_keyword(text, "order")
        extracted.document_creation_date = find_date_by_keyword(text, "document|created|date")

        suppliers = extract_suppliers(text)
        extracted.supplier_name = suppliers[0] if suppliers else None

        invoices = extract_invoice_numbers(text)
        extracted.supplier_invoice_number = invoices[0] if invoices else None

        prices = extract_prices(text)
        for i, ean in enumerate(extracted.eans):
            if i < len(prices):
                extracted.supplier_prices[ean] = prices[i]

        stores = extract_stores(text)
        for i, ean in enumerate(extracted.eans):
            if i < len(stores):
                extracted.stores[ean] = stores[i]

        return extracted

    def _extract_from_pdf_text(self, attachment: EmailAttachment) -> Optional[ExtractedData]:
        """Extract data from PDF text.

        Strategy:
        1. Try pdfplumber extract_tables() for structured table data
        2. Parse tables row by row with header detection
        3. Fallback to plain text extraction if no tables found
        """
        try:
            import pdfplumber
            import io

            pdf_file = io.BytesIO(attachment.content)
        except Exception:
            return None

        try:
            with pdfplumber.open(pdf_file) as pdf:
                # 1. Try structured table extraction first
                table_extracted = self._extract_from_pdf_tables(pdf, attachment.filename)

                # Also get full text for enrichment / fallback
                text = ""
                for page in pdf.pages:
                    text += (page.extract_text() or "") + "\n"
                text = text.strip()

                if table_extracted and table_extracted.eans:
                    # Enrich table data with text-based metadata
                    if text:
                        if not table_extracted.delivery_date:
                            table_extracted.delivery_date = find_date_by_keyword(text, "delivery")
                        if not table_extracted.order_creation_date:
                            table_extracted.order_creation_date = find_date_by_keyword(text, "order")
                        if not table_extracted.document_creation_date:
                            table_extracted.document_creation_date = find_date_by_keyword(text, "document|created|date")
                        if not table_extracted.supplier_name:
                            suppliers = extract_suppliers(text)
                            table_extracted.supplier_name = suppliers[0] if suppliers else None
                        if not table_extracted.supplier_invoice_number:
                            invoices = extract_invoice_numbers(text)
                            table_extracted.supplier_invoice_number = invoices[0] if invoices else None
                    return table_extracted

                # 2. Fallback: plain text extraction
                if not text:
                    return None

                extracted = ExtractedData(
                    source=DataSource.ATTACHMENT,
                    source_details=f"Attachment: {attachment.filename}",
                    eans=extract_eans(text),
                )

                extracted.delivery_date = find_date_by_keyword(text, "delivery")
                extracted.order_creation_date = find_date_by_keyword(text, "order")
                extracted.document_creation_date = find_date_by_keyword(text, "document|created|date")

                suppliers = extract_suppliers(text)
                extracted.supplier_name = suppliers[0] if suppliers else None

                invoices = extract_invoice_numbers(text)
                extracted.supplier_invoice_number = invoices[0] if invoices else None

                prices = extract_prices(text)
                for i, ean in enumerate(extracted.eans):
                    if i < len(prices):
                        extracted.supplier_prices[ean] = prices[i]

                stores = extract_stores(text)
                for i, ean in enumerate(extracted.eans):
                    if i < len(stores):
                        extracted.stores[ean] = stores[i]

                return extracted

        except Exception:
            return None

    def _extract_from_pdf_tables(self, pdf, filename: str) -> Optional[ExtractedData]:
        """Extract structured data from PDF tables using pdfplumber.

        Args:
            pdf: Opened pdfplumber PDF object.
            filename: Original filename for source_details.

        Returns:
            ExtractedData with row-level associations, or None.
        """
        import re as _re

        # Header keywords (similar to Excel structured extractor)
        ean_headers = {"ean", "ean code", "barcode", "bar code", "ean koda", "črtna koda", "barkoda"}
        supplier_price_headers = {
            "supplier price", "purchase price", "cost price", "cena", "vpc", "nc",
            "dobaviteljeva cena", "cena dobavitelja", "nabavna cena", "nab. cena",
        }
        internal_price_headers = {
            "internal price", "our price", "selling price", "retail price", "mpc",
            "naša cena", "prodajna cena", "maloprodajna cena", "prod. cena",
        }
        store_headers = {"store", "unit", "enota", "trgovina", "poslovalnica", "lokacija"}

        for page in pdf.pages:
            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:
                if not table or len(table) < 2:
                    continue

                # Detect header row
                header_row = None
                header_idx = -1
                for idx, row in enumerate(table[:10]):  # Scan first 10 rows
                    if row is None:
                        continue
                    normalized = [
                        _re.sub(r'\s+', ' ', str(c).strip().lower()) if c else ""
                        for c in row
                    ]
                    # Check if any cell matches EAN header
                    has_ean_header = any(
                        any(h in cell or cell in h for h in ean_headers)
                        for cell in normalized if cell
                    )
                    if has_ean_header:
                        header_row = normalized
                        header_idx = idx
                        break

                if header_row is None:
                    continue

                # Map columns
                ean_col = None
                sp_col = None
                ip_col = None
                st_col = None

                for ci, cell in enumerate(header_row):
                    if not cell:
                        continue
                    if any(h in cell or cell in h for h in ean_headers):
                        ean_col = ci
                    elif any(h in cell or cell in h for h in supplier_price_headers):
                        sp_col = ci
                    elif any(h in cell or cell in h for h in internal_price_headers):
                        ip_col = ci
                    elif any(h in cell or cell in h for h in store_headers):
                        st_col = ci

                if ean_col is None:
                    continue

                extracted = ExtractedData(
                    source=DataSource.ATTACHMENT,
                    source_details=f"Attachment: {filename} (structured PDF table)",
                )

                # Parse data rows
                for row in table[header_idx + 1:]:
                    if row is None:
                        continue
                    if all(c is None or str(c).strip() == "" for c in row):
                        continue

                    # Extract EAN
                    if ean_col >= len(row) or row[ean_col] is None:
                        continue
                    ean_text = _re.sub(r'[^\d]', '', str(row[ean_col]).strip())
                    if len(ean_text) not in (8, 13) or not is_valid_ean(ean_text):
                        continue

                    extracted.eans.append(ean_text)

                    # Extract supplier price
                    if sp_col is not None and sp_col < len(row) and row[sp_col] is not None:
                        price = self._parse_price_cell(row[sp_col])
                        if price is not None:
                            extracted.supplier_prices[ean_text] = price

                    # Extract internal price
                    if ip_col is not None and ip_col < len(row) and row[ip_col] is not None:
                        price = self._parse_price_cell(row[ip_col])
                        if price is not None:
                            extracted.internal_prices[ean_text] = price

                    # Extract store
                    if st_col is not None and st_col < len(row) and row[st_col] is not None:
                        store_val = str(row[st_col]).strip()
                        if store_val:
                            extracted.stores[ean_text] = store_val

                if extracted.eans:
                    return extracted

        return None

    @staticmethod
    def _parse_price_cell(cell_value) -> Optional[float]:
        """Parse a price from a PDF table cell."""
        import re as _re

        if isinstance(cell_value, (int, float)):
            val = float(cell_value)
            return val if val > 0 else None

        text = str(cell_value).strip()
        text = _re.sub(r'[€$£\s]', '', text)
        text = text.replace('EUR', '').replace('USD', '').strip()

        if ',' in text and '.' in text:
            text = text.replace('.', '').replace(',', '.')
        elif ',' in text:
            text = text.replace(',', '.')

        try:
            val = float(text)
            return val if val > 0 else None
        except (ValueError, TypeError):
            return None

    def extract_from_body(self, email: EmailItem) -> Optional[ExtractedData]:
        """
        Extract data from email body.

        Strategy:
        1. If HTML body with tables → parse tables structurally (BeautifulSoup)
        2. For remaining text / plain bodies → regex extraction

        Args:
            email: Email item.

        Returns:
            ExtractedData or None.
        """
        body_text = email.body_text or email.body_html or ""

        if not body_text:
            return None

        # 1. Try HTML table extraction if body_html contains <table>
        if email.body_html and "<table" in email.body_html.lower():
            table_extracted = self._extract_from_html_tables(email.body_html)
            if table_extracted and table_extracted.eans:
                # Enrich from full text
                plain_text = email.body_text or ""
                if not plain_text:
                    import re
                    plain_text = re.sub(r'<[^>]+>', ' ', email.body_html)

                if not table_extracted.delivery_date:
                    table_extracted.delivery_date = find_date_by_keyword(plain_text, "delivery")
                if not table_extracted.order_creation_date:
                    table_extracted.order_creation_date = find_date_by_keyword(plain_text, "order")
                if not table_extracted.document_creation_date:
                    table_extracted.document_creation_date = find_date_by_keyword(plain_text, "document|created|date")
                if not table_extracted.supplier_name:
                    suppliers = extract_suppliers(plain_text)
                    table_extracted.supplier_name = suppliers[0] if suppliers else None
                if not table_extracted.supplier_invoice_number:
                    invoices = extract_invoice_numbers(plain_text)
                    table_extracted.supplier_invoice_number = invoices[0] if invoices else None

                return table_extracted

        # 2. Fallback: plain text extraction
        if email.body_html and not email.body_text:
            import re
            body_text = re.sub(r'<[^>]+>', ' ', body_text)

        extracted = ExtractedData(
            source=DataSource.BODY,
            source_details="Email body",
            eans=extract_eans(body_text),
        )

        extracted.delivery_date = find_date_by_keyword(body_text, "delivery")
        extracted.order_creation_date = find_date_by_keyword(body_text, "order")
        extracted.document_creation_date = find_date_by_keyword(body_text, "document|created|date")

        suppliers = extract_suppliers(body_text)
        extracted.supplier_name = suppliers[0] if suppliers else None

        invoices = extract_invoice_numbers(body_text)
        extracted.supplier_invoice_number = invoices[0] if invoices else None

        prices = extract_prices(body_text)
        for i, ean in enumerate(extracted.eans):
            if i < len(prices):
                extracted.supplier_prices[ean] = prices[i]

        stores = extract_stores(body_text)
        for i, ean in enumerate(extracted.eans):
            if i < len(stores):
                extracted.stores[ean] = stores[i]

        return extracted

    def _extract_from_html_tables(self, html: str) -> Optional[ExtractedData]:
        """Extract structured data from HTML tables using BeautifulSoup.

        Args:
            html: HTML body content.

        Returns:
            ExtractedData with row-level associations, or None.
        """
        import re as _re

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return None

        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")

        if not tables:
            return None

        ean_headers = {"ean", "ean code", "barcode", "ean koda", "črtna koda", "barkoda"}
        supplier_price_headers = {
            "supplier price", "purchase price", "cost price", "cena", "vpc", "nc",
            "dobaviteljeva cena", "cena dobavitelja", "nabavna cena",
        }
        internal_price_headers = {
            "internal price", "our price", "selling price", "retail price", "mpc",
            "naša cena", "prodajna cena", "maloprodajna cena",
        }
        store_headers = {"store", "unit", "enota", "trgovina", "poslovalnica", "lokacija"}

        for table in tables:
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue

            # Find header row
            header_row = None
            header_idx = -1
            for idx, row in enumerate(rows[:10]):
                cells = row.find_all(["th", "td"])
                normalized = [
                    _re.sub(r'\s+', ' ', c.get_text().strip().lower())
                    for c in cells
                ]
                has_ean = any(
                    any(h in cell or cell in h for h in ean_headers)
                    for cell in normalized if cell
                )
                if has_ean:
                    header_row = normalized
                    header_idx = idx
                    break

            if header_row is None:
                continue

            # Map columns
            ean_col = None
            sp_col = None
            ip_col = None
            st_col = None

            for ci, cell in enumerate(header_row):
                if not cell:
                    continue
                if any(h in cell or cell in h for h in ean_headers):
                    ean_col = ci
                elif any(h in cell or cell in h for h in supplier_price_headers):
                    sp_col = ci
                elif any(h in cell or cell in h for h in internal_price_headers):
                    ip_col = ci
                elif any(h in cell or cell in h for h in store_headers):
                    st_col = ci

            if ean_col is None:
                continue

            extracted = ExtractedData(
                source=DataSource.BODY,
                source_details="Email body (HTML table)",
            )

            # Parse data rows
            for row in rows[header_idx + 1:]:
                cells = row.find_all(["th", "td"])
                cell_texts = [c.get_text().strip() for c in cells]

                if all(not t for t in cell_texts):
                    continue

                # Extract EAN
                if ean_col >= len(cell_texts):
                    continue
                ean_text = _re.sub(r'[^\d]', '', cell_texts[ean_col])
                if len(ean_text) not in (8, 13) or not is_valid_ean(ean_text):
                    continue

                extracted.eans.append(ean_text)

                # Extract supplier price
                if sp_col is not None and sp_col < len(cell_texts):
                    price = self._parse_price_cell(cell_texts[sp_col])
                    if price is not None:
                        extracted.supplier_prices[ean_text] = price

                # Extract internal price
                if ip_col is not None and ip_col < len(cell_texts):
                    price = self._parse_price_cell(cell_texts[ip_col])
                    if price is not None:
                        extracted.internal_prices[ean_text] = price

                # Extract store
                if st_col is not None and st_col < len(cell_texts) and cell_texts[st_col]:
                    extracted.stores[ean_text] = cell_texts[st_col]

            if extracted.eans:
                return extracted

        return None
