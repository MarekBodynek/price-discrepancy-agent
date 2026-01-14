"""
Microsoft Graph API - Mail operations.
"""

import base64
from datetime import date, datetime
from typing import Optional

import requests

from src.config import Config
from src.core.models import EmailAttachment, EmailItem
from src.integrations.graph.auth import GraphAuthClient
from src.integrations.graph.queries import build_list_messages_params


class GraphMailError(Exception):
    """Graph API mail operation error."""
    pass


class GraphMailClient:
    """Handles mail operations via Microsoft Graph API."""

    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self, config: Config, auth_client: GraphAuthClient):
        """
        Initialize mail client.

        Args:
            config: Application configuration.
            auth_client: Graph authentication client.
        """
        self.config = config
        self.auth_client = auth_client

    def list_unread_messages(
        self,
        date_from: date,
        date_to: date,
    ) -> list[dict]:
        """
        List unread messages in date range.

        Args:
            date_from: Start date (inclusive).
            date_to: End date (inclusive).

        Returns:
            List of message metadata dictionaries.

        Raises:
            GraphMailError: If API request fails.
        """
        url = f"{self.GRAPH_BASE_URL}/users/{self.config.mailbox_user_id}/messages"
        params = build_list_messages_params(
            date_from=date_from,
            date_to=date_to,
            timezone=self.config.timezone,
        )

        all_messages = []

        while url:
            response = requests.get(
                url,
                headers=self.auth_client.get_headers(),
                params=params if url == f"{self.GRAPH_BASE_URL}/users/{self.config.mailbox_user_id}/messages" else None,
            )

            if response.status_code != 200:
                raise GraphMailError(
                    f"Failed to list messages: {response.status_code} {response.text}"
                )

            data = response.json()
            all_messages.extend(data.get("value", []))

            # Handle pagination
            url = data.get("@odata.nextLink")

        return all_messages

    def get_message_body(self, message_id: str) -> tuple[Optional[str], Optional[str]]:
        """
        Get message body (HTML and text).

        Args:
            message_id: Message ID.

        Returns:
            Tuple of (html_body, text_body).

        Raises:
            GraphMailError: If API request fails.
        """
        url = f"{self.GRAPH_BASE_URL}/users/{self.config.mailbox_user_id}/messages/{message_id}"
        params = {"$select": "body,uniqueBody"}

        response = requests.get(
            url,
            headers=self.auth_client.get_headers(),
            params=params,
        )

        if response.status_code != 200:
            raise GraphMailError(
                f"Failed to get message body: {response.status_code} {response.text}"
            )

        data = response.json()
        body = data.get("body", {})
        body_type = body.get("contentType", "text").lower()
        body_content = body.get("content")

        if body_type == "html":
            return body_content, None
        else:
            return None, body_content

    def get_attachments(self, message_id: str) -> list[EmailAttachment]:
        """
        Get message attachments.

        Args:
            message_id: Message ID.

        Returns:
            List of EmailAttachment objects.

        Raises:
            GraphMailError: If API request fails.
        """
        url = f"{self.GRAPH_BASE_URL}/users/{self.config.mailbox_user_id}/messages/{message_id}/attachments"

        response = requests.get(
            url,
            headers=self.auth_client.get_headers(),
        )

        if response.status_code != 200:
            raise GraphMailError(
                f"Failed to get attachments: {response.status_code} {response.text}"
            )

        data = response.json()
        attachments = []

        for item in data.get("value", []):
            attachment_type = item.get("@odata.type")

            # Only handle file attachments (not item attachments)
            if attachment_type == "#microsoft.graph.fileAttachment":
                content_bytes_b64 = item.get("contentBytes", "")
                content_bytes = base64.b64decode(content_bytes_b64)

                attachments.append(
                    EmailAttachment(
                        filename=item.get("name", "unknown"),
                        content_type=item.get("contentType", "application/octet-stream"),
                        content=content_bytes,
                        size=item.get("size", len(content_bytes)),
                    )
                )

        return attachments

    def get_inline_images(self, message_id: str) -> list[EmailAttachment]:
        """
        Get inline images from message body.

        Args:
            message_id: Message ID.

        Returns:
            List of inline images as EmailAttachment objects.

        Raises:
            GraphMailError: If API request fails.
        """
        # Get all attachments
        all_attachments = self.get_attachments(message_id)

        # Filter for images that are inline (isInline flag or image content type)
        inline_images = [
            att
            for att in all_attachments
            if att.content_type.startswith("image/")
        ]

        return inline_images

    def get_email_item(self, message_metadata: dict) -> EmailItem:
        """
        Fetch full email content and convert to EmailItem.

        Args:
            message_metadata: Message metadata from list_unread_messages.

        Returns:
            EmailItem with full content.

        Raises:
            GraphMailError: If API request fails.
        """
        message_id = message_metadata["id"]

        # Get body
        body_html, body_text = self.get_message_body(message_id)

        # Get attachments
        attachments = self.get_attachments(message_id)

        # Separate inline images from regular attachments
        inline_images = [att for att in attachments if att.content_type.startswith("image/")]
        regular_attachments = [att for att in attachments if not att.content_type.startswith("image/")]

        # Parse sender
        sender_obj = message_metadata.get("from", {}).get("emailAddress", {})
        sender_address = sender_obj.get("address", "unknown")

        # Parse received datetime
        received_str = message_metadata.get("receivedDateTime")
        received_datetime = datetime.fromisoformat(received_str.replace("Z", "+00:00"))

        return EmailItem(
            message_id=message_id,
            sender_address=sender_address,
            subject=message_metadata.get("subject", ""),
            received_datetime=received_datetime,
            body_html=body_html,
            body_text=body_text,
            attachments=regular_attachments,
            inline_images=inline_images,
            web_link=message_metadata.get("webLink"),
        )

    def mark_as_read(self, message_id: str) -> None:
        """
        Mark message as read.

        Args:
            message_id: Message ID.

        Raises:
            GraphMailError: If API request fails.
        """
        url = f"{self.GRAPH_BASE_URL}/users/{self.config.mailbox_user_id}/messages/{message_id}"

        response = requests.patch(
            url,
            headers=self.auth_client.get_headers(),
            json={"isRead": True},
        )

        if response.status_code not in (200, 204):
            raise GraphMailError(
                f"Failed to mark message as read: {response.status_code} {response.text}"
            )
