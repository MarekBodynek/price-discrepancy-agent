"""
Query builder for Microsoft Graph API filters.
"""

from datetime import date, datetime, time
from zoneinfo import ZoneInfo


def build_unread_date_filter(
    date_from: date,
    date_to: date,
    timezone: str = "Europe/Ljubljana",
) -> str:
    """
    Build OData filter for unread messages in date range.

    Date range is inclusive (start and end dates included).
    Timezone is used to convert local dates to UTC for Graph API.

    Args:
        date_from: Start date (inclusive).
        date_to: End date (inclusive).
        timezone: Timezone string (e.g., "Europe/Ljubljana").

    Returns:
        OData $filter string.
    """
    tz = ZoneInfo(timezone)

    # Start of day in local timezone
    start_datetime = datetime.combine(date_from, time.min, tzinfo=tz)

    # End of day in local timezone (23:59:59.999999)
    end_datetime = datetime.combine(date_to, time.max, tzinfo=tz)

    # Convert to UTC for Graph API
    start_utc = start_datetime.astimezone(ZoneInfo("UTC"))
    end_utc = end_datetime.astimezone(ZoneInfo("UTC"))

    # Format for Graph API (ISO 8601)
    start_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build OData filter
    filter_parts = [
        "isRead eq false",
        f"receivedDateTime ge {start_str}",
        f"receivedDateTime le {end_str}",
    ]

    return " and ".join(filter_parts)


def build_list_messages_params(
    date_from: date,
    date_to: date,
    timezone: str = "Europe/Ljubljana",
    top: int = 100,
) -> dict[str, str]:
    """
    Build query parameters for listing messages.

    Args:
        date_from: Start date (inclusive).
        date_to: End date (inclusive).
        timezone: Timezone string.
        top: Maximum number of messages per page.

    Returns:
        Dictionary of query parameters.
    """
    return {
        "$filter": build_unread_date_filter(date_from, date_to, timezone),
        "$orderby": "receivedDateTime desc",
        "$top": str(top),
        "$select": "id,subject,from,receivedDateTime,webLink,hasAttachments",
    }
