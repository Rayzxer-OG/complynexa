"""AI-generated certificate name from document text (OpenAI)."""

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Max chars of document text to send (avoid token limits and cost)
MAX_TEXT_FOR_NAMING = 2800


def generate_certificate_name(text: str) -> str | None:
    """
    Use OpenAI to generate a short, proper certificate name from document text.
    Returns a clean title (e.g. "Lifting Machines Examination Report") or None on failure.
    """
    if not text or not text.strip():
        return None
    settings = get_settings()
    if not (settings.openai_api_key and settings.openai_api_key.strip()):
        logger.debug("OPENAI_API_KEY not set; skipping AI certificate name")
        return None

    snippet = text.strip()[:MAX_TEXT_FOR_NAMING]
    prompt = """You are given text extracted from a certificate or test report document.
Your task: suggest ONE short, clear certificate name suitable for a dashboard list.

Rules:
- Do NOT copy the full document heading or title verbatim.
- Produce a concise, readable name in Title Case (e.g. "Lifting Machines Examination Report", "SSL Test Certificate").
- Maximum 60 characters. No quotes, no period at the end, no explanation.
- If the document is about lifting equipment, ropes, tackles, call it something like "Lifting Equipment Examination Report" or "Rope & Lifting Tackles Report".
- Reply with ONLY the certificate name, nothing else."""

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key.strip())
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You reply only with a short certificate name, no other text."},
                {"role": "user", "content": f"{prompt}\n\nDocument text:\n{snippet}"},
            ],
            max_tokens=80,
            temperature=0.3,
        )
        raw = (response.choices[0].message.content or "").strip()
        name = _normalize_ai_name(raw)
        return name if name else None
    except Exception as e:
        logger.warning("OpenAI certificate name generation failed: %s", e)
        return None


def _normalize_ai_name(raw: str) -> str:
    """Remove quotes, trim, enforce max length."""
    s = raw.strip().strip('"\'')
    if not s:
        return ""
    if len(s) > 80:
        s = s[:77] + "..."
    return s
