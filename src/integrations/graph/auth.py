"""
Microsoft Graph API authentication using MSAL (client credentials flow).
"""

from typing import Optional

from msal import ConfidentialClientApplication

from src.config import Config


class GraphAuthError(Exception):
    """Graph API authentication error."""
    pass


class GraphAuthClient:
    """Handles authentication for Microsoft Graph API."""

    GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]

    def __init__(self, config: Config):
        """
        Initialize Graph auth client.

        Args:
            config: Application configuration.
        """
        self.config = config
        self._app: Optional[ConfidentialClientApplication] = None
        self._token: Optional[str] = None

    def get_token(self) -> str:
        """
        Get access token for Microsoft Graph API.

        Returns:
            Access token string.

        Raises:
            GraphAuthError: If authentication fails.
        """
        if self._app is None:
            self._app = ConfidentialClientApplication(
                client_id=self.config.azure_client_id,
                client_credential=self.config.azure_client_secret,
                authority=f"https://login.microsoftonline.com/{self.config.azure_tenant_id}",
            )

        # Try to acquire token from cache first
        result = self._app.acquire_token_silent(
            scopes=self.GRAPH_SCOPES,
            account=None,
        )

        # If not in cache, acquire new token
        if not result:
            result = self._app.acquire_token_for_client(scopes=self.GRAPH_SCOPES)

        if "access_token" not in result:
            error_desc = result.get("error_description", "Unknown error")
            raise GraphAuthError(f"Failed to acquire token: {error_desc}")

        self._token = result["access_token"]
        return self._token

    def get_headers(self) -> dict[str, str]:
        """
        Get HTTP headers with authorization token.

        Returns:
            Dictionary with Authorization header.
        """
        token = self.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
