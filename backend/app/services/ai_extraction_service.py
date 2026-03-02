"""LLM-based compliance field extraction from document text."""

import json
import logging
import re
from typing import Any

from openai import OpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)

CATEGORIES = ("License", "Insurance", "Contract", "Compliance", "Other")

# Words that stay lowercase in title case (except at start/end of phrase)
_TITLE_CASE_MINOR_WORDS = frozenset(
    {"of", "and", "the", "in", "on", "at", "to", "for", "by", "with", "a", "an"}
)

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

OCR_EXTRACTION_PROMPT = """Extract the following fields from the document text below. Return only valid JSON with exactly these keys.

Required JSON shape:
{{
  "document_name": "string or null",
  "license_number": "string or null",
  "signature_person_name": "string or null",
  "signature_designation": "string or null",
  "signing_authority": "string or null",
  "department_or_header": "string or null",
  "unit_name_from_document": "string or null",
  "issue_date": "YYYY-MM-DD or null if not found",
  "expiry_date": "YYYY-MM-DD or null if not found",
  "category": "one of: License | Insurance | Contract | Compliance | Other"
}}

Rules:
- document_name: official name or title of the document.
- license_number: license, certificate, or registration number if present.
- SIGNATURE BLOCK (preferred): Look at the bottom signature section for a block that contains BOTH a person's name and a designation/role. Example pattern: first line "ACHYUT ANAND MISHRA", second line "Member Secretary". Extract: signature_person_name = the full name of the signatory (e.g. "Achyut Anand Mishra"); signature_designation = their title/role (e.g. "Member Secretary", "Chief Inspector of Factories", "Licensing Authority"). Use Title Case; do not use ALL CAPS. If only one of name or designation is present in the signature block, fill only that field.
- signing_authority: Use when the signature block has a single line or you cannot split name and designation. The full signing authority text (e.g. "Chief Inspector of Factories" or "Achyut Anand Mishra, Member Secretary"). Prefer returning signature_person_name + signature_designation when both are present so we can format as "Name, Designation".
- department_or_header: FALLBACK only. The department or office name from the document header/title (e.g. "Directorate of Industrial Health and Safety"). Use only if no signature block with name and/or designation is found. Do not prefer department over signature block.
- unit_name_from_document: The company or factory name as stated on the license. Extract using this priority: (1) Text following "Occupier of" or "Name of factory" or "Company name". (2) Text following "M/s" or "M/s." (the entity name that follows). Return the raw entity name including any prefix; we will normalize it later.
- issue_date: date of issue in YYYY-MM-DD format, or null.
- expiry_date: expiration/valid-until date in YYYY-MM-DD format, or null.
- category: must be exactly one of: License, Insurance, Contract, Compliance, Other.

Document text:
---
{text}
---

Return only the JSON object, no other text."""


def _normalize_issuing_authority_to_title_case(raw: str) -> str:
    """
    Normalize issuing authority to readable Title Case (not ALL CAPS).
    Example: "DIRECTORATE OF INDUSTRIAL HEALTH AND SAFETY" -> "Directorate of Industrial Health and Safety"
    Preserves abbreviations like "Addl." and keeps minor words (of, and, the) lowercase in the middle.
    """
    if not raw or not raw.strip():
        return raw
    s = raw.strip()
    # If already mixed case or lowercase, only normalize minor words
    words = re.split(r"(\s+)", s)
    result: list[str] = []
    for i, w in enumerate(words):
        if not w.strip():
            result.append(w)
            continue
        is_first = not result or all(not x.strip() for x in result)
        is_last = i == len(words) - 1 or all(not words[j].strip() for j in range(i + 1, len(words)))
        lower_w = w.lower()
        if is_first or is_last or lower_w not in _TITLE_CASE_MINOR_WORDS:
            # Capitalize first letter, rest lowercase (handles ALL CAPS)
            if len(w) > 1 and w.isupper():
                result.append(w[0].upper() + w[1:].lower())
            elif len(w) > 0:
                result.append(w[0].upper() + w[1:].lower() if len(w) > 1 else w.upper())
            else:
                result.append(w)
        else:
            result.append(w.lower())
    return "".join(result)


# Company name suffixes: ALL CAPS form -> normalized form (with period where standard)
_UNIT_NAME_SUFFIXES: dict[str, str] = {
    "PVT": "Pvt.",
    "PVT.": "Pvt.",
    "LTD": "Ltd.",
    "LTD.": "Ltd.",
    "LIMITED": "Ltd.",
    "LLP": "LLP",
    "LLC": "LLC",
    "INC": "Inc.",
    "INC.": "Inc.",
    "CORP": "Corp.",
    "CORP.": "Corp.",
    "CORPORATION": "Corp.",
    "CO": "Co.",
    "CO.": "Co.",
    "COMPANY": "Co.",
}

# Prefixes/labels to strip from unit name (case-insensitive)
_UNIT_NAME_PREFIXES = (
    r"^\s*m/s\.?\s*",
    r"^\s*m\/s\.?\s*",
    r"^\s*messrs\.?\s*",
    r"^\s*m\/s\s*",
    r"^\s*name\s+of\s+factory\s*:?\s*",
    r"^\s*company\s+name\s*:?\s*",
    r"^\s*occupier\s+of\s*:?\s*",
)


def _normalize_unit_name(raw: str) -> str:
    """
    Normalize unit/company name from document: remove M/s and Messrs prefixes,
    then apply company-style casing (e.g. BLA POWER PVT LTD -> BLA Power Pvt. Ltd.).
    """
    if not raw or not raw.strip():
        return raw
    s = raw.strip()
    # Remove prefixes (M/s, Messrs, etc.)
    for pat in _UNIT_NAME_PREFIXES:
        s = re.sub(pat, "", s, flags=re.IGNORECASE)
    s = s.strip()
    if not s:
        return s
    words = re.split(r"(\s+)", s)
    result: list[str] = []
    for w in words:
        if not w.strip():
            result.append(w)
            continue
        upper_w = w.upper()
        if upper_w in _UNIT_NAME_SUFFIXES:
            result.append(_UNIT_NAME_SUFFIXES[upper_w])
        elif len(w) <= 4 and w.isupper():
            # Short acronym (e.g. BLA) keep as-is
            result.append(w)
        else:
            # Title case
            result.append(w[0].upper() + w[1:].lower() if len(w) > 1 else w.upper())
    return "".join(result)


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


def _empty_ocr_result() -> dict[str, Any]:
    """Return safe None-valued result for OCR extraction failure."""
    return {
        "document_name": None,
        "license_number": None,
        "issuing_authority": None,
        "issue_date": None,
        "expiry_date": None,
        "unit_name": None,
        "category": None,
    }


def extract_compliance_fields_ocr(text: str) -> dict[str, Any]:
    """
    Extract compliance fields for OCR confirmation flow (license_number, issuing_authority, issue_date, etc.).

    Returns:
        Dict with document_name, license_number, issuing_authority, issue_date, expiry_date, category.
        All values are None on failure or when not found. Dates are YYYY-MM-DD strings or None.
    """
    if not text or not text.strip():
        return _empty_ocr_result()

    settings = get_settings()
    api_key = (settings.openai_api_key or "").strip()
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; skipping OCR compliance extraction")
        return _empty_ocr_result()

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": OCR_EXTRACTION_PROMPT.format(text=text[:12000]),
                }
            ],
            temperature=0,
        )
    except Exception as e:
        logger.exception("OpenAI API error during OCR extraction: %s", e)
        return _empty_ocr_result()

    content = (response.choices[0].message.content or "").strip()
    if not content:
        return _empty_ocr_result()

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
        logger.warning("Invalid JSON from LLM (OCR): %s", e)
        return _empty_ocr_result()

    def str_or_none(v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip() or None
        return str(v).strip() or None

    document_name = str_or_none(data.get("document_name"))
    license_number = str_or_none(data.get("license_number"))
    signature_person_name = str_or_none(data.get("signature_person_name"))
    signature_designation = str_or_none(data.get("signature_designation"))
    signing_authority = str_or_none(data.get("signing_authority"))
    department_or_header = str_or_none(data.get("department_or_header"))
    issue_date = str_or_none(data.get("issue_date"))
    expiry_date = str_or_none(data.get("expiry_date"))
    category = data.get("category")
    if category not in CATEGORIES:
        category = None

    # Issuing authority: prefer full signature (person name + designation), then signing_authority, then department
    # Build full authority as "Name, Designation" when both are present; otherwise use single value
    raw_authority: str | None = None
    if signature_person_name and signature_designation:
        raw_authority = f"{signature_person_name}, {signature_designation}"
        logger.debug("Combined signature_person_name + signature_designation: %s", raw_authority)
    elif signature_person_name:
        raw_authority = signature_person_name
    elif signature_designation:
        raw_authority = signature_designation
    if not raw_authority:
        raw_authority = signing_authority or department_or_header or str_or_none(data.get("issuing_authority"))
    if raw_authority:
        issuing_authority = _normalize_issuing_authority_to_title_case(raw_authority)
        if signature_person_name or signature_designation:
            logger.debug("Using signature block for issuing_authority: %s", issuing_authority)
        elif signing_authority:
            logger.debug("Using signing_authority for issuing_authority: %s", issuing_authority)
        elif department_or_header:
            logger.debug("Using department_or_header fallback for issuing_authority: %s", issuing_authority)
    else:
        issuing_authority = None

    # Unit/company name: extract from document, strip M/s/Messrs, normalize casing (e.g. PVT LTD -> Pvt. Ltd.)
    raw_unit = str_or_none(data.get("unit_name_from_document"))
    if raw_unit:
        unit_name = _normalize_unit_name(raw_unit)
        logger.debug("Extracted and normalized unit_name from document: %s", unit_name)
    else:
        unit_name = None

    return {
        "document_name": document_name,
        "license_number": license_number,
        "issuing_authority": issuing_authority,
        "issue_date": issue_date,
        "expiry_date": expiry_date,
        "unit_name": unit_name,
        "category": category,
    }
