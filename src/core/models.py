"""
Data models for email processing.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class ProcessStatus(Enum):
    """Email processing status."""
    PROCESSED = "PROCESSED"
    SKIPPED_BUSINESS_ERROR = "SKIPPED_BUSINESS_ERROR"
    SKIPPED_TECHNICAL_ERROR = "SKIPPED_TECHNICAL_ERROR"


class ErrorType(Enum):
    """Error type classification."""
    BUSINESS = "BUSINESS"  # Missing mandatory data (e.g., no delivery/order date)
    TECHNICAL = "TECHNICAL"  # Technical failure (e.g., API error, OCR failure)
    UNEXPECTED = "UNEXPECTED"  # Unexpected exception


class DataSource(Enum):
    """Source of extracted data (for priority merge)."""
    OCR = "OCR"  # Images (inline, attachments, PDF images)
    ATTACHMENT = "ATTACHMENT"  # Excel/PDF text attachments
    BODY = "BODY"  # Email body text


@dataclass
class EmailAttachment:
    """Email attachment metadata."""
    filename: str
    content_type: str
    content: bytes
    size: int


@dataclass
class EmailItem:
    """Represents a single email message."""
    message_id: str
    sender_address: str
    subject: str
    received_datetime: datetime
    body_html: Optional[str]
    body_text: Optional[str]
    attachments: list[EmailAttachment] = field(default_factory=list)
    inline_images: list[EmailAttachment] = field(default_factory=list)
    web_link: Optional[str] = None


@dataclass
class ExtractedData:
    """Data extracted from a single source (OCR/attachment/body)."""
    source: DataSource
    source_details: str  # e.g., "OCR: image1.png", "Attachment: report.xlsx"

    # Extracted fields
    eans: list[str] = field(default_factory=list)
    delivery_date: Optional[date] = None
    order_creation_date: Optional[date] = None
    document_creation_date: Optional[date] = None
    supplier_name: Optional[str] = None
    supplier_invoice_number: Optional[str] = None
    supplier_prices: dict[str, float] = field(default_factory=dict)  # EAN -> price
    internal_prices: dict[str, float] = field(default_factory=dict)  # EAN -> price
    stores: dict[str, str] = field(default_factory=dict)  # EAN -> store/unit


@dataclass
class CaseRow:
    """
    Single row in the output Excel file (one EAN).
    Column order must match README requirements.
    """
    unit_store: str  # 1. Unit (Store)
    ean_code: str  # 2. EAN Code
    document_creation_date: Optional[date]  # 3. Document Creation Date
    delivery_date: Optional[date]  # 4. Delivery Date
    order_creation_date: Optional[date]  # 5. Order Creation Date
    supplier_price: Optional[float]  # 6. Supplier Price
    internal_price: Optional[float]  # 7. Internal (Own) Price
    supplier_name: Optional[str]  # 8. Supplier Name
    supplier_invoice_number: Optional[str]  # 9. Supplier Invoice Number
    email_sender_address: str  # 10. Email Sender Address
    email_link: Optional[str]  # 11. Email Link / Stable Reference
    comments: str  # 12. Comments (conflicts, notes)


@dataclass
class EmailProcessResult:
    """Result of processing a single email."""
    email_item: EmailItem
    status: ProcessStatus
    error_type: Optional[ErrorType] = None
    error_message: Optional[str] = None
    cases: list[CaseRow] = field(default_factory=list)
    marked_as_read: bool = False


@dataclass
class RunResult:
    """Result of entire pipeline run."""
    run_timestamp: datetime
    date_from: date
    date_to: date
    emails_processed: int = 0
    emails_skipped: int = 0
    cases_extracted: int = 0
    excel_filename: Optional[str] = None
    log_filename: Optional[str] = None
    sharepoint_upload_success: bool = False
