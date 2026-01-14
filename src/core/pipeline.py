"""
Main processing pipeline.
"""

from datetime import date, datetime
from typing import Optional

from src.config import Config
from src.core.extractors import DataExtractor
from src.core.models import (
    CaseRow,
    EmailItem,
    EmailProcessResult,
    ErrorType,
    ExtractedData,
    ProcessStatus,
    RunResult,
)
from src.core.normalize import Normalizers
from src.core.priority import PriorityMerger
from src.core.validators import ValidationError, Validators
from src.integrations.graph.auth import GraphAuthClient
from src.integrations.graph.mail import GraphMailClient


def process_single_email(
    email: EmailItem,
    config: Config,
    dry_run: bool = False,
) -> EmailProcessResult:
    """
    Process a single email.

    Args:
        email: Email item to process.
        config: Application configuration.
        dry_run: If True, don't mark email as read.

    Returns:
        EmailProcessResult with status and cases.
    """
    try:
        # Initialize extractor
        extractor = DataExtractor(config)

        # Extract from all sources
        extractions = []

        # 1. OCR (highest priority)
        ocr_data = extractor.extract_from_ocr(email)
        if ocr_data:
            extractions.append(ocr_data)

        # 2. Attachments
        attachment_data = extractor.extract_from_attachments(email)
        extractions.extend(attachment_data)

        # 3. Body (lowest priority)
        body_data = extractor.extract_from_body(email)
        if body_data:
            extractions.append(body_data)

        # Merge extractions by priority
        merger = PriorityMerger()
        merged_data, conflicts = merger.merge_all(extractions)

        # Validate mandatory date gate (HARD STOP)
        try:
            Validators.validate_mandatory_date_gate(merged_data)
        except ValidationError as e:
            # BUSINESS ERROR - skip email, leave UNREAD
            return EmailProcessResult(
                email_item=email,
                status=ProcessStatus.SKIPPED_BUSINESS_ERROR,
                error_type=ErrorType.BUSINESS,
                error_message=str(e),
                cases=[],
                marked_as_read=False,
            )

        # Generate case rows (one per EAN)
        cases = generate_case_rows(email, merged_data, conflicts)

        # Success - email will be marked as read (if not dry-run)
        return EmailProcessResult(
            email_item=email,
            status=ProcessStatus.PROCESSED,
            error_type=None,
            error_message=None,
            cases=cases,
            marked_as_read=not dry_run,
        )

    except Exception as e:
        # TECHNICAL ERROR - skip email, leave UNREAD, continue processing
        return EmailProcessResult(
            email_item=email,
            status=ProcessStatus.SKIPPED_TECHNICAL_ERROR,
            error_type=ErrorType.TECHNICAL,
            error_message=str(e),
            cases=[],
            marked_as_read=False,
        )


def generate_case_rows(
    email: EmailItem,
    merged_data: ExtractedData,
    conflicts: list[str],
) -> list[CaseRow]:
    """
    Generate case rows from merged data.

    Args:
        email: Email item.
        merged_data: Merged extracted data.
        conflicts: List of conflict descriptions.

    Returns:
        List of CaseRow objects (one per EAN).
    """
    cases = []

    # If no EANs, create single row with available data
    eans = merged_data.eans if merged_data.eans else ["UNKNOWN"]

    for ean in eans:
        # Normalize data
        normalized_ean = Normalizers.normalize_ean(ean)

        # Get EAN-specific data
        store = merged_data.stores.get(ean)
        supplier_price = merged_data.supplier_prices.get(ean)
        internal_price = merged_data.internal_prices.get(ean)

        # Normalize
        normalized_store = Normalizers.normalize_store(store) or "UNKNOWN"
        normalized_supplier_price = (
            Normalizers.normalize_price(supplier_price) if supplier_price else None
        )
        normalized_internal_price = (
            Normalizers.normalize_price(internal_price) if internal_price else None
        )

        # Build comments
        comments_parts = []

        # Add data source info
        comments_parts.append(f"Sources: {merged_data.source_details}")

        # Add conflicts
        if conflicts:
            comments_parts.append("Conflicts: " + "; ".join(conflicts))

        # Add OCR usage note
        if "OCR" in merged_data.source_details:
            comments_parts.append("Used OCR for extraction")

        comments = " | ".join(comments_parts)

        # Create case row
        case = CaseRow(
            unit_store=normalized_store,
            ean_code=normalized_ean,
            document_creation_date=merged_data.document_creation_date,
            delivery_date=merged_data.delivery_date,
            order_creation_date=merged_data.order_creation_date,
            supplier_price=normalized_supplier_price,
            internal_price=normalized_internal_price,
            supplier_name=Normalizers.normalize_supplier_name(merged_data.supplier_name),
            supplier_invoice_number=Normalizers.normalize_invoice_number(
                merged_data.supplier_invoice_number
            ),
            email_sender_address=email.sender_address,
            email_link=email.web_link,
            comments=comments,
        )

        cases.append(case)

    return cases


def run_pipeline(
    config: Config,
    date_from: date,
    date_to: date,
    dry_run: bool = False,
) -> RunResult:
    """
    Run the main processing pipeline.

    Args:
        config: Application configuration.
        date_from: Start date (inclusive).
        date_to: End date (inclusive).
        dry_run: If True, don't mark emails as read or upload to SharePoint.

    Returns:
        RunResult with statistics.
    """
    run_timestamp = datetime.now()

    # Initialize Graph API clients
    auth_client = GraphAuthClient(config)
    mail_client = GraphMailClient(config, auth_client)

    # Get unread messages in date range
    print(f"Fetching unread messages from {date_from} to {date_to}...")
    messages_metadata = mail_client.list_unread_messages(date_from, date_to)
    print(f"Found {len(messages_metadata)} unread messages")

    # Process each email
    results: list[EmailProcessResult] = []

    for i, msg_metadata in enumerate(messages_metadata, 1):
        print(f"\nProcessing email {i}/{len(messages_metadata)}: {msg_metadata.get('subject', 'No subject')}")

        try:
            # Fetch full email content
            email = mail_client.get_email_item(msg_metadata)

            # Process email
            result = process_single_email(email, config, dry_run)

            results.append(result)

            # Mark as read if processed successfully (and not dry-run)
            if result.status == ProcessStatus.PROCESSED and result.marked_as_read:
                try:
                    mail_client.mark_as_read(email.message_id)
                    print(f"  ✓ Processed: {len(result.cases)} cases extracted, marked as read")
                except Exception as e:
                    print(f"  ! Failed to mark as read: {e}")
            elif result.status == ProcessStatus.SKIPPED_BUSINESS_ERROR:
                print(f"  ✗ Skipped (BUSINESS): {result.error_message}")
            elif result.status == ProcessStatus.SKIPPED_TECHNICAL_ERROR:
                print(f"  ✗ Skipped (TECHNICAL): {result.error_message}")

        except Exception as e:
            # Unexpected error - log and continue
            print(f"  ✗ Unexpected error: {e}")
            results.append(
                EmailProcessResult(
                    email_item=EmailItem(
                        message_id=msg_metadata.get("id", "unknown"),
                        sender_address=msg_metadata.get("from", {}).get("emailAddress", {}).get("address", "unknown"),
                        subject=msg_metadata.get("subject", ""),
                        received_datetime=datetime.now(),
                        body_html=None,
                        body_text=None,
                    ),
                    status=ProcessStatus.SKIPPED_TECHNICAL_ERROR,
                    error_type=ErrorType.UNEXPECTED,
                    error_message=str(e),
                    cases=[],
                    marked_as_read=False,
                )
            )

    # Calculate statistics
    emails_processed = sum(1 for r in results if r.status == ProcessStatus.PROCESSED)
    emails_skipped = len(results) - emails_processed

    # Collect all cases from all emails
    all_cases = []
    for result in results:
        all_cases.extend(result.cases)

    cases_extracted = len(all_cases)

    # Generate Excel and log files
    from src.integrations.excel.writer import ExcelWriter
    from src.integrations.logging.run_log import RunLogWriter
    from src.integrations.graph.sharepoint import GraphSharePointClient
    import tempfile
    from pathlib import Path

    excel_filename = None
    log_filename = None
    sharepoint_upload_success = False

    if cases_extracted > 0 or not dry_run:
        # Generate filenames
        excel_writer = ExcelWriter()
        log_writer = RunLogWriter()

        excel_filename = excel_writer.generate_filename(date_from, date_to)
        log_filename = log_writer.generate_filename(run_timestamp)

        # Create temp directory for outputs
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Write Excel file
            excel_path = temp_path / excel_filename
            if cases_extracted > 0:
                excel_writer.write_report(all_cases, str(excel_path), date_from, date_to)
                print(f"\nGenerated Excel report: {excel_filename}")
            else:
                # Create empty Excel if no cases
                excel_writer.write_report([], str(excel_path), date_from, date_to)
                print(f"\nGenerated empty Excel report: {excel_filename}")

            # Write log file
            log_path = temp_path / log_filename
            log_writer.write_log(results, str(log_path), run_timestamp)
            print(f"Generated log file: {log_filename}")

            # Upload to SharePoint (if not dry-run)
            if not dry_run:
                try:
                    sharepoint_client = GraphSharePointClient(config, auth_client)

                    # Upload Excel
                    final_excel_name = sharepoint_client.upload_file(
                        str(excel_path),
                        filename=excel_filename,
                        handle_collision=True,
                    )
                    print(f"Uploaded Excel to SharePoint: {final_excel_name}")

                    # Upload log
                    final_log_name = sharepoint_client.upload_file(
                        str(log_path),
                        filename=log_filename,
                        handle_collision=True,
                    )
                    print(f"Uploaded log to SharePoint: {final_log_name}")

                    sharepoint_upload_success = True
                    excel_filename = final_excel_name
                    log_filename = final_log_name

                except Exception as e:
                    print(f"Failed to upload to SharePoint: {e}")
                    sharepoint_upload_success = False
            else:
                print("Dry run mode: Skipping SharePoint upload")

    # Create run result
    run_result = RunResult(
        run_timestamp=run_timestamp,
        date_from=date_from,
        date_to=date_to,
        emails_processed=emails_processed,
        emails_skipped=emails_skipped,
        cases_extracted=cases_extracted,
        excel_filename=excel_filename,
        log_filename=log_filename,
        sharepoint_upload_success=sharepoint_upload_success,
    )

    return run_result
