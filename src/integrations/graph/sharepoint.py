"""
Microsoft Graph API - SharePoint operations.
"""

from pathlib import Path
from typing import Optional

import requests

from src.config import Config
from src.integrations.graph.auth import GraphAuthClient


class GraphSharePointError(Exception):
    """Graph API SharePoint operation error."""
    pass


class GraphSharePointClient:
    """Handles SharePoint operations via Microsoft Graph API."""

    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self, config: Config, auth_client: GraphAuthClient):
        """
        Initialize SharePoint client.

        Args:
            config: Application configuration.
            auth_client: Graph authentication client.
        """
        self.config = config
        self.auth_client = auth_client

    def _check_file_exists(self, filename: str) -> bool:
        """
        Check if file exists in SharePoint folder.

        Args:
            filename: File name to check.

        Returns:
            True if file exists, False otherwise.
        """
        folder_path = self.config.sharepoint_folder_path.strip("/")
        url = (
            f"{self.GRAPH_BASE_URL}/sites/{self.config.sharepoint_site_id}"
            f"/drives/{self.config.sharepoint_drive_id}/root:/{folder_path}/{filename}"
        )

        response = requests.get(
            url,
            headers=self.auth_client.get_headers(),
        )

        return response.status_code == 200

    def _generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate unique filename with _v2, _v3, etc. suffix if needed.

        Args:
            original_filename: Original file name.

        Returns:
            Unique filename (may be same as original if no collision).
        """
        if not self._check_file_exists(original_filename):
            return original_filename

        # Split name and extension
        path = Path(original_filename)
        stem = path.stem
        suffix = path.suffix

        # Try _v2, _v3, etc.
        version = 2
        while True:
            new_filename = f"{stem}_v{version}{suffix}"
            if not self._check_file_exists(new_filename):
                return new_filename
            version += 1

            # Safety limit
            if version > 100:
                raise GraphSharePointError(
                    f"Too many versions of file {original_filename}"
                )

    def upload_file(
        self,
        local_path: str,
        filename: Optional[str] = None,
        handle_collision: bool = True,
    ) -> str:
        """
        Upload file to SharePoint folder.

        Args:
            local_path: Path to local file.
            filename: Target filename (default: use local filename).
            handle_collision: If True, add _v2, _v3 suffix on collision.

        Returns:
            Final filename used in SharePoint.

        Raises:
            GraphSharePointError: If upload fails.
        """
        local_file = Path(local_path)

        if not local_file.exists():
            raise GraphSharePointError(f"File not found: {local_path}")

        # Determine target filename
        target_filename = filename or local_file.name

        # Handle collision if needed
        if handle_collision:
            target_filename = self._generate_unique_filename(target_filename)

        # Upload file
        folder_path = self.config.sharepoint_folder_path.strip("/")
        url = (
            f"{self.GRAPH_BASE_URL}/sites/{self.config.sharepoint_site_id}"
            f"/drives/{self.config.sharepoint_drive_id}/root:/{folder_path}/{target_filename}:/content"
        )

        with open(local_file, "rb") as f:
            file_content = f.read()

        # Use PUT for files <= 4MB (simple upload)
        response = requests.put(
            url,
            headers={
                **self.auth_client.get_headers(),
                "Content-Type": "application/octet-stream",
            },
            data=file_content,
        )

        if response.status_code not in (200, 201):
            raise GraphSharePointError(
                f"Failed to upload file: {response.status_code} {response.text}"
            )

        return target_filename

    def upload_content(
        self,
        content: bytes,
        filename: str,
        handle_collision: bool = True,
    ) -> str:
        """
        Upload file content to SharePoint folder.

        Args:
            content: File content as bytes.
            filename: Target filename.
            handle_collision: If True, add _v2, _v3 suffix on collision.

        Returns:
            Final filename used in SharePoint.

        Raises:
            GraphSharePointError: If upload fails.
        """
        # Handle collision if needed
        if handle_collision:
            filename = self._generate_unique_filename(filename)

        # Upload content
        folder_path = self.config.sharepoint_folder_path.strip("/")
        url = (
            f"{self.GRAPH_BASE_URL}/sites/{self.config.sharepoint_site_id}"
            f"/drives/{self.config.sharepoint_drive_id}/root:/{folder_path}/{filename}:/content"
        )

        response = requests.put(
            url,
            headers={
                **self.auth_client.get_headers(),
                "Content-Type": "application/octet-stream",
            },
            data=content,
        )

        if response.status_code not in (200, 201):
            raise GraphSharePointError(
                f"Failed to upload content: {response.status_code} {response.text}"
            )

        return filename
