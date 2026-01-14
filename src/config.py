"""
Configuration loader and validator.
Loads settings from .env file and validates required values.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class ConfigError(Exception):
    """Configuration error."""
    pass


@dataclass
class Config:
    """Application configuration."""

    # Azure / Graph API
    azure_tenant_id: str
    azure_client_id: str
    azure_client_secret: str

    # Mailbox
    mailbox_user_id: str

    # SharePoint
    sharepoint_site_id: str
    sharepoint_drive_id: str
    sharepoint_folder_path: str

    # OCR
    tesseract_path: str
    poppler_path: str
    ocr_languages: list[str]

    # Claude API (optional)
    anthropic_api_key: Optional[str]

    # Timezone
    timezone: str

    # Logging
    log_level: str


def load_config() -> Config:
    """
    Load configuration from .env file.

    Raises:
        ConfigError: If required configuration is missing or invalid.
    """
    # Load .env from project root
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"

    if not env_path.exists():
        raise ConfigError(
            f".env file not found at {env_path}. "
            "Copy .env.example to .env and fill in the values."
        )

    load_dotenv(env_path)

    # Required fields
    required_fields = {
        "AZURE_TENANT_ID": "azure_tenant_id",
        "AZURE_CLIENT_ID": "azure_client_id",
        "AZURE_CLIENT_SECRET": "azure_client_secret",
        "MAILBOX_USER_ID": "mailbox_user_id",
        "SHAREPOINT_SITE_ID": "sharepoint_site_id",
        "SHAREPOINT_DRIVE_ID": "sharepoint_drive_id",
        "SHAREPOINT_FOLDER_PATH": "sharepoint_folder_path",
        "TESSERACT_PATH": "tesseract_path",
        "POPPLER_PATH": "poppler_path",
    }

    config_dict = {}
    missing = []

    for env_var, field_name in required_fields.items():
        value = os.getenv(env_var)
        if not value or value.strip() == "":
            missing.append(env_var)
        else:
            config_dict[field_name] = value.strip()

    if missing:
        raise ConfigError(
            f"Missing required configuration: {', '.join(missing)}. "
            f"Please set these values in .env file."
        )

    # Optional fields with defaults
    config_dict["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY", "").strip() or None
    config_dict["timezone"] = os.getenv("TIMEZONE", "Europe/Ljubljana").strip()
    config_dict["log_level"] = os.getenv("LOG_LEVEL", "INFO").strip().upper()

    # OCR languages (parse comma-separated list)
    ocr_langs_str = os.getenv("OCR_LANGUAGES", "eng,slv").strip()
    config_dict["ocr_languages"] = [lang.strip() for lang in ocr_langs_str.split(",") if lang.strip()]

    # Validate paths
    tesseract_path = Path(config_dict["tesseract_path"])
    if not tesseract_path.exists():
        raise ConfigError(f"Tesseract not found at {tesseract_path}")

    poppler_path = Path(config_dict["poppler_path"])
    if not poppler_path.exists():
        raise ConfigError(f"Poppler not found at {poppler_path}")

    return Config(**config_dict)
