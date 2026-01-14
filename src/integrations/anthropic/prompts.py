"""
Claude prompts for data extraction fallback.

CRITICAL RULES:
- Never invent data
- Never fill in missing values
- Never interpret intent
- Only work with explicitly provided text
"""

EXTRACTION_SYSTEM_PROMPT = """You are a data extraction assistant. Your job is to extract structured data from text.

CRITICAL RULES:
1. NEVER invent or guess data that is not explicitly present in the text
2. NEVER fill in missing values with assumptions
3. NEVER interpret intent or context beyond what is written
4. If data is ambiguous or unclear, return null/empty
5. Only extract data that is explicitly stated in the source text

You must be conservative and precise. When in doubt, return nothing rather than guessing."""


def build_field_extraction_prompt(field_name: str, text: str, context: str = "") -> str:
    """
    Build prompt for extracting a specific field.

    Args:
        field_name: Name of field to extract (e.g., "delivery_date", "ean_codes").
        text: Source text to analyze.
        context: Additional context (optional).

    Returns:
        Prompt string.
    """
    prompt = f"""Extract the {field_name} from the following text.

RULES:
- Only extract if EXPLICITLY present in the text
- Do NOT guess or infer
- Do NOT fill in missing values
- Return null if not found or ambiguous

Text:
{text}

"""

    if context:
        prompt += f"Context: {context}\n\n"

    prompt += f"""Respond with ONLY the extracted value in this format:
{{
  "{field_name}": <value or null>
}}

If multiple values are found, return as array.
If nothing found or ambiguous, return null."""

    return prompt


def build_conflict_resolution_prompt(
    field_name: str,
    values: list[str],
    sources: list[str],
) -> str:
    """
    Build prompt for resolving conflicts between values.

    Args:
        field_name: Name of field.
        values: List of conflicting values.
        sources: List of source descriptions.

    Returns:
        Prompt string.
    """
    prompt = f"""Multiple values found for {field_name} from different sources:

"""

    for i, (value, source) in enumerate(zip(values, sources), 1):
        prompt += f"{i}. From {source}: {value}\n"

    prompt += f"""
RULES:
- Do NOT invent a new value
- Do NOT average or combine values
- Select the most reliable value based on source credibility
- OCR sources are less reliable than structured attachments
- If values are contradictory and equally credible, return null

Respond with ONLY the best value in this format:
{{
  "{field_name}": <selected value or null>,
  "reason": "<brief explanation>"
}}
"""

    return prompt


def build_structured_extraction_prompt(text: str) -> str:
    """
    Build prompt for extracting all structured data at once.

    Args:
        text: Source text.

    Returns:
        Prompt string.
    """
    return f"""Extract structured data from the following text for a price discrepancy case.

RULES:
- Only extract explicitly present data
- NEVER guess or infer
- Return null for missing fields
- Dates in ISO format (YYYY-MM-DD)
- Prices as numbers (no currency symbols)

Text:
{text}

Respond with JSON in this exact format:
{{
  "ean_codes": [<list of EAN codes found, or empty array>],
  "delivery_date": "<date or null>",
  "order_creation_date": "<date or null>",
  "document_creation_date": "<date or null>",
  "supplier_name": "<name or null>",
  "supplier_invoice_number": "<number or null>",
  "supplier_prices": {{"<ean>": <price>, ...}},
  "internal_prices": {{"<ean>": <price>, ...}},
  "stores": {{"<ean>": "<store>", ...}}
}}

Return ONLY valid JSON. No explanations."""
