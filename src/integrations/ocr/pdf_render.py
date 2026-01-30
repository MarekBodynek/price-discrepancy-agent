"""
PDF rendering to images using Poppler (pdftoppm).
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from src.config import Config


class PDFRenderError(Exception):
    """PDF rendering error."""
    pass


class PDFRenderer:
    """Renders PDF pages to PNG images using Poppler."""

    def __init__(self, config: Config):
        """
        Initialize PDF renderer.

        Args:
            config: Application configuration.
        """
        self.config = config
        # Cross-platform: use .exe on Windows, no extension on macOS/Linux
        binary_name = "pdftoppm.exe" if sys.platform == "win32" else "pdftoppm"
        self.pdftoppm_path = Path(config.poppler_path) / binary_name

        if not self.pdftoppm_path.exists():
            raise PDFRenderError(f"pdftoppm not found at {self.pdftoppm_path}")

    def render_pdf_to_images(
        self,
        pdf_content: bytes,
        dpi: int = 300,
    ) -> list[bytes]:
        """
        Render all pages of PDF to PNG images.

        Args:
            pdf_content: PDF file content as bytes.
            dpi: Resolution for rendering (default 300).

        Returns:
            List of PNG image bytes (one per page).

        Raises:
            PDFRenderError: If rendering fails.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Write PDF to temp file
            pdf_file = temp_path / "input.pdf"
            pdf_file.write_bytes(pdf_content)

            # Output prefix for rendered images
            output_prefix = temp_path / "page"

            # Run pdftoppm
            try:
                subprocess.run(
                    [
                        str(self.pdftoppm_path),
                        "-png",
                        "-r",
                        str(dpi),
                        str(pdf_file),
                        str(output_prefix),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                raise PDFRenderError(
                    f"pdftoppm failed: {e.stderr}"
                ) from e
            except FileNotFoundError as e:
                raise PDFRenderError(
                    f"pdftoppm executable not found at {self.pdftoppm_path}"
                ) from e

            # Collect rendered PNG files
            png_files = sorted(temp_path.glob("page-*.png"))

            if not png_files:
                raise PDFRenderError("No pages rendered from PDF")

            # Read all PNG files
            images = []
            for png_file in png_files:
                images.append(png_file.read_bytes())

            return images

    def render_pdf_page(
        self,
        pdf_content: bytes,
        page_number: int,
        dpi: int = 300,
    ) -> Optional[bytes]:
        """
        Render a single page of PDF to PNG.

        Args:
            pdf_content: PDF file content as bytes.
            page_number: Page number (1-indexed).
            dpi: Resolution for rendering.

        Returns:
            PNG image bytes, or None if page doesn't exist.

        Raises:
            PDFRenderError: If rendering fails.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Write PDF to temp file
            pdf_file = temp_path / "input.pdf"
            pdf_file.write_bytes(pdf_content)

            # Output prefix for rendered image
            output_prefix = temp_path / "page"

            # Run pdftoppm for single page
            try:
                subprocess.run(
                    [
                        str(self.pdftoppm_path),
                        "-png",
                        "-r",
                        str(dpi),
                        "-f",
                        str(page_number),
                        "-l",
                        str(page_number),
                        str(pdf_file),
                        str(output_prefix),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                raise PDFRenderError(
                    f"pdftoppm failed: {e.stderr}"
                ) from e

            # Find rendered PNG file
            png_files = list(temp_path.glob("page-*.png"))

            if not png_files:
                return None

            return png_files[0].read_bytes()
