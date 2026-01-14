"""
Claude API client (fallback for ambiguous cases).

IMPORTANT: Claude is used as a fallback when deterministic extraction is unclear.
Claude NEVER invents data, NEVER fills in missing values, NEVER interprets intent.
"""

import json
from typing import Optional

import anthropic

from src.config import Config
from src.integrations.anthropic.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    build_conflict_resolution_prompt,
    build_field_extraction_prompt,
    build_structured_extraction_prompt,
)


class ClaudeClient:
    """Client for Claude API (Anthropic)."""

    def __init__(self, config: Config):
        """
        Initialize Claude client.

        Args:
            config: Application configuration.
        """
        self.config = config
        self.api_key = config.anthropic_api_key

        if not self.api_key:
            raise ValueError("Claude API key not configured in .env")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"

    def clarify_extraction(
        self,
        text: str,
        field_name: str,
        context: str = "",
    ) -> Optional[str]:
        """
        Ask Claude to clarify ambiguous extraction.

        RULES:
        - Claude works ONLY with provided text
        - Claude does NOT invent data
        - Claude does NOT fill in missing values
        - Claude does NOT interpret intent beyond explicit text

        Args:
            text: Source text to analyze.
            field_name: Name of field to extract.
            context: Additional context (optional).

        Returns:
            Clarified value or None if cannot be determined.
        """
        prompt = build_field_extraction_prompt(field_name, text, context)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=EXTRACTION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text

            # Parse JSON response
            try:
                result = json.loads(response_text)
                return result.get(field_name)
            except json.JSONDecodeError:
                # If not valid JSON, return None
                return None

        except Exception as e:
            # On error, return None (fallback failed)
            print(f"Claude API error: {e}")
            return None

    def resolve_conflict(
        self,
        field_name: str,
        values: list[str],
        sources: list[str],
    ) -> Optional[str]:
        """
        Ask Claude to resolve conflict between multiple values.

        Args:
            field_name: Name of field.
            values: List of conflicting values.
            sources: List of source descriptions.

        Returns:
            Best value or None if cannot determine.
        """
        prompt = build_conflict_resolution_prompt(field_name, values, sources)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=EXTRACTION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text

            # Parse JSON response
            try:
                result = json.loads(response_text)
                return result.get(field_name)
            except json.JSONDecodeError:
                return None

        except Exception as e:
            print(f"Claude API error: {e}")
            return None

    def extract_structured_data(self, text: str) -> Optional[dict]:
        """
        Extract all structured data at once using Claude.

        Args:
            text: Source text.

        Returns:
            Dictionary with extracted fields or None.
        """
        prompt = build_structured_extraction_prompt(text)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=EXTRACTION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text

            # Parse JSON response
            try:
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                return None

        except Exception as e:
            print(f"Claude API error: {e}")
            return None
