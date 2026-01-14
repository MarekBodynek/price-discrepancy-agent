"""
Tests for config module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.config import Config, ConfigError, load_config


def test_config_missing_env_file():
    """Test that missing .env file raises ConfigError."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory with no .env
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            with pytest.raises(ConfigError) as exc_info:
                load_config()

            assert ".env file not found" in str(exc_info.value)
        finally:
            os.chdir(original_cwd)


def test_config_missing_required_fields():
    """Test that missing required fields raises ConfigError."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create incomplete .env file
        env_path = Path(temp_dir) / ".env"
        env_path.write_text("AZURE_TENANT_ID=test-tenant\n")  # Missing other fields

        # Mock Path to return our temp .env
        with patch("src.config.Path") as mock_path:
            mock_path.return_value.parent.parent = Path(temp_dir)

            with pytest.raises(ConfigError) as exc_info:
                load_config()

            assert "Missing required configuration" in str(exc_info.value)


def test_config_invalid_tesseract_path():
    """Test that invalid Tesseract path raises ConfigError."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create real .env file in temp dir
        env_path = Path(temp_dir) / ".env"
        env_content = """
AZURE_TENANT_ID=test-tenant
AZURE_CLIENT_ID=test-client
AZURE_CLIENT_SECRET=test-secret
MAILBOX_USER_ID=test@example.com
SHAREPOINT_SITE_ID=test-site
SHAREPOINT_DRIVE_ID=test-drive
SHAREPOINT_FOLDER_PATH=/test
TESSERACT_PATH=/invalid/path/tesseract.exe
POPPLER_PATH=/invalid/path/poppler
"""
        env_path.write_text(env_content)

        # Mock Path(__file__).parent.parent to return temp_dir
        with patch("src.config.Path") as mock_path:
            # __file__ in config.py should point to temp_dir
            mock_file_path = Mock()
            mock_file_path.parent.parent = Path(temp_dir)
            mock_path.return_value = mock_file_path

            # But also allow Path() calls for tesseract/poppler validation
            # These will use real Path() and check existence
            def path_side_effect(arg):
                if arg == "/invalid/path/tesseract.exe" or arg == "/invalid/path/poppler":
                    return Path(arg)  # Real Path - will fail exists()
                return mock_file_path

            mock_path.side_effect = path_side_effect

            with pytest.raises(ConfigError) as exc_info:
                load_config()

            assert "Tesseract not found" in str(exc_info.value)
