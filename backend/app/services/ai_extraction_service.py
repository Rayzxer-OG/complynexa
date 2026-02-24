"""LLM-based compliance field extraction from document text."""

import json
import logging
from typing import Any

from openai import OpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)

CATEGORIES = ("License", "Insurance", "Contract", "Compliance", "Other")

EXTRACTION_PROMPT = """Extract the following fields from the document text below. Return only valid JSON with exactly these keys.

Required JSON shape:
{{
  "document_name": "string or null",
  "expiry_date": "YYYY-MM-DD or null if not found",
  "category": "one of: License | Insurance | Contract | Compliance | Other"
}}

Rules:
- document_name: official name or title of the document.
- expiry_date: expiration/valid-until date in YYYY-MM-DD format, or null.
- category: must be exactly one of: License, Insurance, Contract, Compliance, Other.

Document text:
---
{text}
---

Return only the JSON object, no other text."""


def _empty_result() -> dict[str, Any]:
    """Return safe None-valued result on extraction failure."""
    return {
        "document_name": None,
        "expiry_date": None,
        "category": None,
    }


def extract_compliance_fields(text: str) -> dict[str, Any]:
    """
    Extract structured compliance fields from document text using OpenAI.

    Args:
        text: Raw extracted text (e.g. from Textract).

    Returns:
        Dict with keys document_name, expiry_date, category.
        Values are None on failure or when not found.
        expiry_date is YYYY-MM-DD string or None.
        category is one of License | Insurance | Contract | Compliance | Other or None.
    """
    if not text or not text.strip():
        return _empty_result()

    settings = get_settings()
    api_key = (settings.openai_api_key or "").strip()
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; skipping compliance extraction")
        return _empty_result()

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(text=text[:12000]),
                }
            ],
            temperature=0,
        )
    except Exception as e:
        logger.exception("OpenAI API error during compliance extraction: %s", e)
        return _empty_result()

    content = (response.choices[0].message.content or "").strip()
    if not content:
        return _empty_result()

    # Strip markdown code block if present
    if content.startswith("```"):
        lines = content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON from LLM: %s", e)
        return _empty_result()

    document_name = data.get("document_name")
    expiry_date = data.get("expiry_date")
    category = data.get("category")

    if document_name is not None and not isinstance(document_name, str):
        document_name = str(document_name) if document_name else None
    if expiry_date is not None and not isinstance(expiry_date, str):
        expiry_date = None
    if category is not None:
        if not isinstance(category, str):
            category = None
        elif category not in CATEGORIES:
            category = None

    return {
        "document_name": document_name or None,
        "expiry_date": expiry_date or None,
        "category": category or None,
    }
