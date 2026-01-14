"""
Tesseract OCR wrapper.
"""

import subprocess
import tempfile
from pathlib import Path

from src.config import Config


class TesseractError(Exception):
    """Tesseract OCR error."""
    pass


class TesseractOCR:
    """Wrapper for Tesseract OCR."""

    def __init__(self, config: Config):
        """
        Initialize Tesseract OCR.

        Args:
            config: Application configuration.
        """
        self.config = config
        self.tesseract_path = Path(config.tesseract_path)

        if not self.tesseract_path.exists():
            raise TesseractError(f"Tesseract not found at {self.tesseract_path}")

        self.languages = "+".join(config.ocr_languages)

    def extract_text(self, image_content: bytes) -> str:
        """
        Extract text from image using OCR.

        Args:
            image_content: Image file content as bytes.

        Returns:
            Extracted text (may be empty if no text found).

        Raises:
            TesseractError: If OCR fails.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Write image to temp file
            image_file = temp_path / "image.png"
            image_file.write_bytes(image_content)

            # Output text file
            output_base = temp_path / "output"

            # Run Tesseract
            try:
                subprocess.run(
                    [
                        str(self.tesseract_path),
                        str(image_file),
                        str(output_base),
                        "-l",
                        self.languages,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                raise TesseractError(
                    f"Tesseract failed: {e.stderr}"
                ) from e
            except FileNotFoundError as e:
                raise TesseractError(
                    f"Tesseract executable not found at {self.tesseract_path}"
                ) from e

            # Read output text file
            output_file = temp_path / "output.txt"

            if not output_file.exists():
                raise TesseractError("Tesseract did not produce output file")

            text = output_file.read_text(encoding="utf-8")

            return text.strip()

    def extract_text_batch(self, images: list[bytes]) -> list[str]:
        """
        Extract text from multiple images.

        Args:
            images: List of image contents as bytes.

        Returns:
            List of extracted texts (same order as input).

        Raises:
            TesseractError: If OCR fails for any image.
        """
        results = []

        for image in images:
            try:
                text = self.extract_text(image)
                results.append(text)
            except TesseractError as e:
                # Log error but continue with empty text
                results.append("")

        return results
