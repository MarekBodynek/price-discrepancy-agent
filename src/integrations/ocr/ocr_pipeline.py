"""
OCR pipeline orchestration.
"""

from dataclasses import dataclass

from src.config import Config
from src.core.models import EmailItem
from src.integrations.ocr.image_extract import ImageExtractor, ImageSource
from src.integrations.ocr.tesseract import TesseractOCR


@dataclass
class OCRResult:
    """Result of OCR processing."""
    source_name: str
    text: str
    success: bool
    error: str = ""


class OCRPipeline:
    """Orchestrates OCR processing for emails."""

    def __init__(self, config: Config):
        """
        Initialize OCR pipeline.

        Args:
            config: Application configuration.
        """
        self.config = config
        self.image_extractor = ImageExtractor(config)
        self.tesseract = TesseractOCR(config)

    def process_email(self, email: EmailItem) -> list[OCRResult]:
        """
        Process all images in email with OCR.

        Args:
            email: Email item.

        Returns:
            List of OCR results (one per image).
        """
        # Extract all images
        images = self.image_extractor.extract_all_images(email)

        if not images:
            return []

        # Run OCR on all images
        results = []

        for img_source in images:
            try:
                text = self.tesseract.extract_text(img_source.content)
                results.append(
                    OCRResult(
                        source_name=img_source.source_name,
                        text=text,
                        success=True,
                    )
                )
            except Exception as e:
                results.append(
                    OCRResult(
                        source_name=img_source.source_name,
                        text="",
                        success=False,
                        error=str(e),
                    )
                )

        return results

    def get_combined_ocr_text(self, email: EmailItem) -> str:
        """
        Get combined OCR text from all images in email.

        Args:
            email: Email item.

        Returns:
            Combined OCR text with source annotations.
        """
        results = self.process_email(email)

        if not results:
            return ""

        # Combine all OCR texts with source markers
        combined_parts = []

        for result in results:
            if result.success and result.text:
                combined_parts.append(f"[OCR from {result.source_name}]")
                combined_parts.append(result.text)
                combined_parts.append("")  # Empty line separator

        return "\n".join(combined_parts)
