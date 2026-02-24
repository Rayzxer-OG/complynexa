"""LLM-based extraction of certificate/report fields from document text (OpenAI)."""

import json
import logging
from datetime import date

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Max chars to send to LLM
MAX_TEXT_LENGTH = 6000
MAX_STRUCTURE_TEXT_LENGTH = 20000


def detect_document_structure_llm(text: str) -> dict:
    """
    Ask LLM to determine if document is single_certificate (e.g. insurance policy)
    or multi_certificate (e.g. inspection report with multiple reports).
    Returns dict with document_type, certificate_count, report_numbers.
    On failure returns dict with document_type "single_certificate" as safe default.
    """
    if not text or not text.strip():
        return {"document_type": "single_certificate", "certificate_count": 1, "report_numbers": []}
    settings = get_settings()
    if not (settings.openai_api_key and settings.openai_api_key.strip()):
        logger.debug("OPENAI_API_KEY not set; defaulting to single_certificate")
        return {"document_type": "single_certificate", "certificate_count": 1, "report_numbers": []}

    snippet = text.strip()[:MAX_STRUCTURE_TEXT_LENGTH]
    prompt = f"""
You are analyzing a compliance document that may be EITHER:
A) One single document (e.g. one insurance policy, one certificate) spanning multiple pages
B) Multiple separate certificates/reports in one PDF (e.g. inspection report with REPORT No. 01, REPORT No. 02, ... each on its own page or section)

CRITICAL RULE:
- Search the ENTIRE text for "REPORT No." or "Report No." or "Certificate No." followed by a number or code (e.g. MG/SSL/TESTING-01, MG/SSL/TESTING-02).
- If you find 2 or more DISTINCT report/certificate numbers (e.g. TESTING-01 and TESTING-02 and TESTING-03), the document is multi_certificate.
- Only return single_certificate if there is clearly ONE certificate/policy (one report number, or none, or the same number repeated on every page).

Return valid JSON only, no other text:

{{
  "document_type": "single_certificate" or "multi_certificate",
  "certificate_count": number (must be 2 or more when document_type is multi_certificate),
  "report_numbers": list of every report number found, e.g. ["MG/SSL/TESTING-01", "MG/SSL/TESTING-02", "MG/SSL/TESTING-03"]
}}

Document text:
{snippet}
"""

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key.strip())
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": "You analyze compliance documents. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
        )
        content = (response.choices[0].message.content or "").strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        data = json.loads(content)
        if not isinstance(data, dict):
            return {"document_type": "single_certificate", "certificate_count": 1, "report_numbers": []}
        doc_type = data.get("document_type") or "single_certificate"
        if doc_type not in ("single_certificate", "multi_certificate"):
            doc_type = "single_certificate"
        return {
            "document_type": doc_type,
            "certificate_count": data.get("certificate_count") if isinstance(data.get("certificate_count"), int) else (1 if doc_type == "single_certificate" else 0),
            "report_numbers": data.get("report_numbers") if isinstance(data.get("report_numbers"), list) else [],
        }
    except json.JSONDecodeError as e:
        logger.warning("LLM structure detection JSON parse failed: %s", e)
        return {"document_type": "single_certificate", "certificate_count": 1, "report_numbers": []}
    except Exception as e:
        logger.warning("LLM structure detection failed: %s", e)
        return {"document_type": "single_certificate", "certificate_count": 1, "report_numbers": []}


def _parse_iso_date(s: str | None) -> date | None:
    """Parse YYYY-MM-DD string to date, or return None."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    if len(s) < 10:
        return None
    try:
        return date(int(s[:4]), int(s[5:7]), int(s[8:10]))
    except (ValueError, TypeError):
        return None


def extract_certificate_data_llm(text: str) -> dict:
    """
    Use OpenAI to extract structured compliance data from document text.
    Returns dict with keys: certificate_name, report_number, issue_date, expiry_date.
    Dates are returned as YYYY-MM-DD strings; caller may convert to date objects.
    On failure returns empty dict or partial dict; regex fallback should be used.
    """
    if not text or not text.strip():
        return {}
    settings = get_settings()
    if not (settings.openai_api_key and settings.openai_api_key.strip()):
        logger.debug("OPENAI_API_KEY not set; skipping LLM extraction")
        return {}

    snippet = text.strip()[:MAX_TEXT_LENGTH]
    prompt = f"""
You are an expert compliance document parser.

Extract certificate information.

Normalize certificate_name using these rules:

If certificate contains:
- "Power Press" → use "Examination of Power Press and Safety Devices"
- "Pressure Vessel" → use "Report of Examination of Pressure Vessel"
- "Lifting Machine" → use "Examination of Lifting Machines"
- Insurance Policy → use "Insurance Policy Certificate"

Use consistent naming.

Return valid JSON only with these keys (use null for missing values):
* certificate_name
* report_number
* issue_date (YYYY-MM-DD)
* expiry_date (YYYY-MM-DD)

Document text:
{snippet}
"""

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key.strip())
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": "Extract structured compliance data. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
        )
        content = (response.choices[0].message.content or "").strip()
        # Strip markdown code block if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        data = json.loads(content)
        if not isinstance(data, dict):
            return {}
        return data
    except json.JSONDecodeError as e:
        logger.warning("LLM extraction JSON parse failed: %s", e)
        return {}
    except Exception as e:
        logger.warning("LLM extraction failed: %s", e)
        return {}


def extract_certificate_data_llm_with_dates(text: str) -> dict:
    """
    Same as extract_certificate_data_llm but parses issue_date and expiry_date
    to date objects. Keys in result: certificate_name, report_number, issue_date (date | None), expiry_date (date | None).
    """
    raw = extract_certificate_data_llm(text)
    result = {
        "certificate_name": raw.get("certificate_name") if isinstance(raw.get("certificate_name"), str) else None,
        "report_number": raw.get("report_number") if isinstance(raw.get("report_number"), str) else None,
        "issue_date": _parse_iso_date(raw.get("issue_date")) if raw.get("issue_date") is not None else None,
        "expiry_date": _parse_iso_date(raw.get("expiry_date")) if raw.get("expiry_date") is not None else None,
    }
    return result
