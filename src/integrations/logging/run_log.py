"""
Run log writer.

Writes per-run log file with processing results.
"""

from datetime import datetime
from pathlib import Path

from src.core.models import EmailProcessResult, ProcessStatus


class RunLogWriter:
    """Writes run log files."""

    def __init__(self):
        """Initialize log writer."""
        pass

    def write_log(
        self,
        results: list[EmailProcessResult],
        output_path: str,
        run_timestamp: datetime,
    ) -> None:
        """
        Write processing log.

        Args:
            results: List of email processing results.
            output_path: Output file path.
            run_timestamp: Timestamp of run start.
        """
        with open(output_path, "w", encoding="utf-8") as f:
            # Write header
            f.write("=" * 80 + "\n")
            f.write("Price Discrepancy Email Processor - Run Log\n")
            f.write("=" * 80 + "\n")
            f.write(f"Run timestamp: {run_timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total emails: {len(results)}\n")
            f.write("\n")

            # Write summary
            processed = sum(1 for r in results if r.status == ProcessStatus.PROCESSED)
            skipped_business = sum(
                1 for r in results if r.status == ProcessStatus.SKIPPED_BUSINESS_ERROR
            )
            skipped_technical = sum(
                1 for r in results if r.status == ProcessStatus.SKIPPED_TECHNICAL_ERROR
            )

            f.write("Summary:\n")
            f.write(f"  Processed: {processed}\n")
            f.write(f"  Skipped (Business Error): {skipped_business}\n")
            f.write(f"  Skipped (Technical Error): {skipped_technical}\n")
            f.write("\n")

            # Write per-email details
            f.write("=" * 80 + "\n")
            f.write("Email Processing Details\n")
            f.write("=" * 80 + "\n\n")

            for i, result in enumerate(results, 1):
                f.write(f"Email {i}/{len(results)}\n")
                f.write(f"  Sender: {result.email_item.sender_address}\n")
                f.write(f"  Subject: {result.email_item.subject}\n")
                f.write(f"  Received: {result.email_item.received_datetime.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"  Status: {result.status.value}\n")

                if result.error_type:
                    f.write(f"  Error Type: {result.error_type.value}\n")
                    f.write(f"  Error Message: {result.error_message}\n")

                if result.status == ProcessStatus.PROCESSED:
                    f.write(f"  Cases Extracted: {len(result.cases)}\n")
                    f.write(f"  Marked as Read: {result.marked_as_read}\n")

                f.write("\n")

            # Write footer
            f.write("=" * 80 + "\n")
            f.write("End of Log\n")
            f.write("=" * 80 + "\n")

    @staticmethod
    def generate_filename(run_timestamp: datetime) -> str:
        """
        Generate filename for log file.

        Args:
            run_timestamp: Timestamp of run.

        Returns:
            Filename string.
        """
        return f"Run_Log_{run_timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
