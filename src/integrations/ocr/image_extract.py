"""
Image extraction from email sources.
"""

from dataclasses import dataclass
from typing import Optional

from src.config import Config
from src.core.models import EmailAttachment, EmailItem
from src.integrations.ocr.pdf_render import PDFRenderer


@dataclass
class ImageSource:
    """Represents an image with its source metadata."""
    content: bytes
    source_name: str  # e.g., "inline:image1.png", "attachment:report.pdf:page1"
    original_filename: Optional[str] = None


class ImageExtractor:
    """Extracts images from various email sources."""

    def __init__(self, config: Config):
        """
        Initialize image extractor.

        Args:
            config: Application configuration.
        """
        self.config = config
        self.pdf_renderer = PDFRenderer(config)

    def extract_inline_images(self, email: EmailItem) -> list[ImageSource]:
        """
        Extract inline images from email.

        Args:
            email: Email item.

        Returns:
            List of image sources.
        """
        images = []

        for img in email.inline_images:
            images.append(
                ImageSource(
                    content=img.content,
                    source_name=f"inline:{img.filename}",
                    original_filename=img.filename,
                )
            )

        return images

    def extract_attachment_images(self, email: EmailItem) -> list[ImageSource]:
        """
        Extract image attachments (JPG, PNG) from email.

        Args:
            email: Email item.

        Returns:
            List of image sources.
        """
        images = []

        for att in email.attachments:
            # Check if it's an image
            if att.content_type.startswith("image/"):
                images.append(
                    ImageSource(
                        content=att.content,
                        source_name=f"attachment:{att.filename}",
                        original_filename=att.filename,
                    )
                )

        return images

    def extract_pdf_images(self, email: EmailItem) -> list[ImageSource]:
        """
        Extract images from PDF attachments (render pages).

        Args:
            email: Email item.

        Returns:
            List of image sources (one per page).
        """
        images = []

        for att in email.attachments:
            # Check if it's a PDF
            if att.content_type == "application/pdf" or att.filename.lower().endswith(".pdf"):
                try:
                    # Render all pages to images
                    page_images = self.pdf_renderer.render_pdf_to_images(att.content)

                    for i, page_img in enumerate(page_images, start=1):
                        images.append(
                            ImageSource(
                                content=page_img,
                                source_name=f"attachment:{att.filename}:page{i}",
                                original_filename=att.filename,
                            )
                        )
                except Exception as e:
                    # Skip this PDF if rendering fails
                    pass

        return images

    def extract_all_images(self, email: EmailItem) -> list[ImageSource]:
        """
        Extract all images from email (inline, attachments, PDFs).

        Args:
            email: Email item.

        Returns:
            List of all image sources.
        """
        all_images = []

        # Priority order: inline, then attachments, then PDF pages
        all_images.extend(self.extract_inline_images(email))
        all_images.extend(self.extract_attachment_images(email))
        all_images.extend(self.extract_pdf_images(email))

        return all_images
