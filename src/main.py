"""
Price Discrepancy Email Processor - CLI entrypoint.

Usage:
    python -m src.main --date 2024-01-15
    python -m src.main --date-from 2024-01-15 --date-to 2024-01-20
    python -m src.main --auto  (last 24 hours)
    python -m src.main --date 2024-01-15 --dry-run
"""

import argparse
import sys
from datetime import date, datetime, timedelta

from src.config import load_config, ConfigError


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process unread Outlook emails for price discrepancies.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument(
        "--date",
        type=str,
        help="Single date to process (YYYY-MM-DD format)",
    )
    date_group.add_argument(
        "--auto",
        action="store_true",
        help="Automatic mode: process last 24 hours",
    )

    parser.add_argument(
        "--date-from",
        type=str,
        help="Start date for range (YYYY-MM-DD format, inclusive)",
    )
    parser.add_argument(
        "--date-to",
        type=str,
        help="End date for range (YYYY-MM-DD format, inclusive)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode: no mark-as-read, no SharePoint upload",
    )

    args = parser.parse_args()

    # Validate date arguments
    if args.date and (args.date_from or args.date_to):
        parser.error("Cannot use --date with --date-from/--date-to")

    if (args.date_from and not args.date_to) or (args.date_to and not args.date_from):
        parser.error("Both --date-from and --date-to must be specified together")

    return args


def parse_date(date_str: str) -> date:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD.")


def get_date_range(args: argparse.Namespace) -> tuple[date, date]:
    """Get date range from arguments."""
    if args.auto:
        # Last 24 hours - today and yesterday
        today = date.today()
        yesterday = today - timedelta(days=1)
        return yesterday, today

    if args.date:
        single_date = parse_date(args.date)
        return single_date, single_date

    # Range mode
    if args.date_from and args.date_to:
        date_from = parse_date(args.date_from)
        date_to = parse_date(args.date_to)
        if date_from > date_to:
            raise ValueError("--date-from cannot be after --date-to")
        return date_from, date_to

    raise ValueError("No valid date arguments provided")


def main() -> int:
    """Main entry point."""
    try:
        args = parse_args()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1

    # Load configuration
    try:
        config = load_config()
    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    # Parse date range
    try:
        date_from, date_to = get_date_range(args)
    except ValueError as e:
        print(f"Date error: {e}", file=sys.stderr)
        return 1

    # Display run info
    print("=" * 60)
    print("Price Discrepancy Email Processor")
    print("=" * 60)
    print(f"Date range: {date_from} to {date_to} (inclusive)")
    print(f"Dry run: {args.dry_run}")
    print(f"Mailbox: {config.mailbox_user_id}")
    print("=" * 60)

    # Run pipeline (stub for now)
    from src.core.pipeline import run_pipeline

    try:
        result = run_pipeline(
            config=config,
            date_from=date_from,
            date_to=date_to,
            dry_run=args.dry_run,
        )
        print(f"\nProcessing complete.")
        print(f"Emails processed: {result.emails_processed}")
        print(f"Emails skipped: {result.emails_skipped}")
        print(f"Cases extracted: {result.cases_extracted}")
        return 0

    except Exception as e:
        print(f"Pipeline error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
