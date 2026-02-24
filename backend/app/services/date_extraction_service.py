"""Semantic date extraction from certificate text (issue vs expiry)."""

import re
from datetime import date
from typing import NamedTuple

# Priority patterns for expiry (search in order; first match wins for expiry)
# Indian testing certs often use "Valid Upto", "Next Due", etc.
EXPIRY_PATTERNS = [
    r"next\s+testing\s+due\s+on",
    r"next\s+test(?:ing)?\s+due",
    r"testing\s+due\s+on",
    r"next\s+due\s+date",
    r"next\s+due",
    r"valid\s+upto",
    r"valid\s+up\s+to",
    r"expiry\s+date",
    r"date\s+of\s+expiry",
    r"due\s+date",
    r"renewal\s+date",
    r"valid\s+until",
    r"valid\s+till",
    r"validity\s+until",
    r"validity",
]

# Patterns for issue date (Indian testing reports: "Date of Issue", "Tested on", etc.)
ISSUE_PATTERNS = [
    r"i\s+certify\s+that\s+on",
    r"date\s+of\s+issue",
    r"issue\s+date",
    r"issued\s+on",
    r"issued\s+date",
    r"certified\s+on",
    r"tested\s+on",
    r"date\s+of\s+test",
    r"date\s+of\s+testing",
    r"date\s+of\s+examination",
    r"examination\s+date",
]

# Regex to capture a date (YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, DD Month YYYY)
DATE_PATTERN = re.compile(
    r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"
    r"|"
    r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b"
    r"|"
    r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b"
    r"|"
    r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b"
    r"|"
    r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\b",
    re.IGNORECASE,
)

MONTH_NAMES_TO_NUM = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


class ExtractedDates(NamedTuple):
    """Issue and expiry dates extracted from text."""

    issue_date: date | None
    expiry_date: date | None


def _parse_date_from_match(m: re.Match) -> date | None:
    """Parse the first three groups into a date (YYYY-MM-DD, D/M/Y, D.M.Y, or DD Month YYYY)."""
    groups = m.groups()
    parts = [g for g in groups if g is not None]
    if len(parts) < 2:
        return None
    try:
        if len(parts) == 3:
            a, b, c = parts[0], parts[1], parts[2]
            # DD Month YYYY (b is month name)
            if b.isalpha():
                day = int(a)
                year = int(c)
                month_num = MONTH_NAMES_TO_NUM.get(b[:3].lower())
                if month_num and 1 <= day <= 31 and year > 1000:
                    return date(year, month_num, day)
            # numeric (YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY)
            a, b, c = int(a), int(b), int(c)
            if a > 1000 and 1 <= b <= 12 and 1 <= c <= 31:
                return date(a, b, c)  # YYYY-MM-DD
            if 1 <= a <= 31 and 1 <= b <= 12 and c > 1000:
                return date(c, b, a)  # DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
    except (ValueError, TypeError):
        pass
    return None


def _find_date_after_pattern(text: str, pattern: re.Pattern) -> date | None:
    """Find the first date that appears after the given pattern in text."""
    for m in pattern.finditer(text, re.IGNORECASE):
        # Search for a date in the rest of the text after this match (wider window for multi-line)
        start = m.end()
        snippet = text[start : start + 350]
        date_m = DATE_PATTERN.search(snippet)
        if date_m:
            return _parse_date_from_match(date_m)
    return None


def _find_all_dates(text: str) -> list[date]:
    """Find all parseable dates in text, in order of appearance."""
    if not text or not text.strip():
        return []
    seen: set[tuple[int, int, int]] = set()
    result: list[date] = []
    for m in DATE_PATTERN.finditer(text):
        d = _parse_date_from_match(m)
        if d and (d.year, d.month, d.day) not in seen:
            seen.add((d.year, d.month, d.day))
            result.append(d)
    return result


def extract_issue_and_expiry(text: str) -> ExtractedDates:
    """
    Extract issue_date and expiry_date using semantic keyword detection.
    If no keyword-based dates found, fallback: use first date as issue, last as expiry.
    """
    if not text or not text.strip():
        return ExtractedDates(issue_date=None, expiry_date=None)

    issue_date: date | None = None
    expiry_date: date | None = None

    for pat in ISSUE_PATTERNS:
        r = re.compile(pat, re.IGNORECASE)
        issue_date = _find_date_after_pattern(text, r)
        if issue_date is not None:
            break

    for pat in EXPIRY_PATTERNS:
        r = re.compile(pat, re.IGNORECASE)
        expiry_date = _find_date_after_pattern(text, r)
        if expiry_date is not None:
            break

    # Fallback: use first and last date in document when keyword extraction found nothing
    if issue_date is None or expiry_date is None:
        all_dates = _find_all_dates(text)
        if all_dates:
            if issue_date is None:
                issue_date = all_dates[0]
            if expiry_date is None:
                expiry_date = all_dates[-1] if len(all_dates) > 1 else all_dates[0]
            # If we only had one date, use it for issue; leave expiry as that or None
            if len(all_dates) == 1 and expiry_date is None:
                expiry_date = all_dates[0]

    return ExtractedDates(issue_date=issue_date, expiry_date=expiry_date)


def extract_report_number(text: str) -> str | None:
    """Extract full REPORT No. value from text (e.g. 'REPORT No. MG/SSL/TESTING-01')."""
    # Capture full value until double space, newline, or end of string (avoids truncation)
    m = re.search(
        r"REPORT\s+No\.?\s*[:\s]*([A-Za-z0-9\-/\s_]+?)(?=\s{2,}|\r?\n|$)",
        text,
        re.IGNORECASE,
    )
    if not m:
        m = re.search(r"REPORT\s+No\.?\s*[:\s]*([A-Za-z0-9\-/\s_]+)", text, re.IGNORECASE)
    return m.group(1).strip() if m else None


# Patterns for certificate/report type (label before the actual type name)
CERT_TYPE_LABEL_PATTERNS = [
    r"type\s+of\s+certificate\s*[:\s]*\n?\s*([^\n]{2,80})",
    r"certificate\s+type\s*[:\s]*\n?\s*([^\n]{2,80})",
    r"nature\s+of\s+test\s*[:\s]*\n?\s*([^\n]{2,80})",
    r"type\s+of\s+test\s*[:\s]*\n?\s*([^\n]{2,80})",
    r"report\s+type\s*[:\s]*\n?\s*([^\n]{2,80})",
    r"type\s+of\s+report\s*[:\s]*\n?\s*([^\n]{2,80})",
    r"test\s+type\s*[:\s]*\n?\s*([^\n]{2,80})",
]
# Phrases that introduce the cert/report type as the following phrase
CERT_TYPE_PHRASE_PATTERNS = [
    r"certificate\s+of\s+([^\n\.]{2,60})",
    r"test\s+report\s+for\s+([^\n\.]{2,60})",
    r"report\s+for\s+([^\n\.]{2,60})",
    r"report\s+on\s+([^\n\.]{2,60})",
    r"certificate\s+for\s+([^\n\.]{2,60})",
]


def _clean_cert_name(raw: str) -> str:
    """Trim and limit length; drop if it looks like a report number only."""
    s = raw.strip()
    if not s or len(s) < 2:
        return ""
    # If it's only something like "MG/SSL/TESTING-01", don't use as display name
    if re.match(r"^[A-Z0-9/\-\s]+$", s, re.IGNORECASE) and "/" in s and len(s) < 30:
        return ""
    return s[:120].strip()


def extract_certificate_name(text: str) -> str | None:
    """
    Extract certificate/report type (e.g. 'Lift Testing', 'SSL Certificate') from text.
    Prefers explicit labels like 'Type of Certificate' / 'Nature of Test'; then phrases
    like 'Certificate of X' / 'Test Report for X'; then a title-style line (not report no.).
    Returns None if nothing meaningful found, so caller can fall back to report_number.
    """
    if not text or not text.strip():
        return None

    # 1) Label-based: "Type of Certificate : Lift Installation"
    for pat in CERT_TYPE_LABEL_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            name = _clean_cert_name(m.group(1))
            if name:
                return name

    # 2) Phrase-based: "Certificate of Conformity", "Test Report for Lift Testing"
    for pat in CERT_TYPE_PHRASE_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            name = _clean_cert_name(m.group(1))
            if name:
                return name

    # 3) Title-style line: first line that looks like a heading (e.g. "Lift Testing Certificate")
    skip_words = {"certificate", "report", "page", "no.", "date", "valid", "test"}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines:
        if re.search(r"REPORT\s+No\.?", line, re.IGNORECASE):
            continue
        if len(line) < 5 or re.match(r"^[\d\s\.\-/]+$", line):
            continue
        words = line.split()
        if len(words) < 2 or len(words) > 12 or len(line) > 80:
            continue
        if words[0].lower() in skip_words and len(words) <= 2:
            continue
        cleaned = _clean_cert_name(line)
        if not cleaned:
            continue
        if "/" in cleaned and re.match(r"^[A-Z0-9/\-\s]+$", cleaned, re.IGNORECASE):
            continue
        return cleaned

    return None
