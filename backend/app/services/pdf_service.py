"""PDF splitting service (split by document-identifier pattern, only when value changes)."""

import logging
import re
from io import BytesIO

from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

# Patterns that may indicate a document/certificate identifier (pattern + value).
# We split only when the VALUE changes from page to page (e.g. REPORT No. 01 -> 02 -> 03).
# If the same value appears on every page (e.g. Certificate No. 12345 on all pages), treat as one document.
DOC_ID_PATTERNS = [
    (re.compile(r"REPORT\s+No\.?\s*[:\s]*([A-Za-z0-9\-/\s_]+?)(?=\s{2,}|\r?\n|$)", re.I), "REPORT No."),
    (re.compile(r"CERTIFICATE\s+No\.?\s*[:\s]*([A-Za-z0-9\-/\s_]+?)(?=\s{2,}|\r?\n|$)", re.I), "Certificate No."),
    (re.compile(r"CERT\.?\s+No\.?\s*[:\s]*([A-Za-z0-9\-/\s_]+?)(?=\s{2,}|\r?\n|$)", re.I), "Cert No."),
    (re.compile(r"POLICY\s+No\.?\s*[:\s]*([A-Za-z0-9\-/\s_]+?)(?=\s{2,}|\r?\n|$)", re.I), "Policy No."),
    (re.compile(r"DOCUMENT\s+No\.?\s*[:\s]*([A-Za-z0-9\-/\s_]+?)(?=\s{2,}|\r?\n|$)", re.I), "Document No."),
]


def _extract_doc_id_from_text(text: str) -> str | None:
    """Extract first matching document identifier value from text. Normalized for comparison."""
    if not text or not text.strip():
        return None
    for pat, _ in DOC_ID_PATTERNS:
        m = pat.search(text)
        if m:
            val = m.group(1).strip()
            if val and len(val) <= 80:
                return val
    return None


class PDFServiceError(Exception):
    """Raised when PDF operations fail."""

    pass


def find_certificate_start_pages(pdf_bytes: bytes) -> list[int]:
    """
    Find 0-based page indices where a new document starts.

    Uses REPORT No., Certificate No., Policy No., etc. Only treats a page as a new
    start when the identifier VALUE changes from the previous page. So:
    - Same "Certificate No. 12345" on every page -> one document (start_pages = [0]).
    - "REPORT No. 01", "REPORT No. 02", ... on successive pages -> one start per report.
    """
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as e:
        raise PDFServiceError(f"Failed to read PDF: {e}") from e

    num_pages = len(reader.pages)
    page_ids: list[str | None] = []
    for page in reader.pages:
        text = page.extract_text()
        page_ids.append(_extract_doc_id_from_text(text or ""))

    start_pages: list[int] = [0]
    for i in range(1, num_pages):
        curr = page_ids[i]
        prev = page_ids[i - 1]
        # New document only when the identifier value changes from previous page
        if curr is not None and prev is not None and curr != prev:
            start_pages.append(i)

    print("Total PDF pages:", num_pages)
    print("Document start pages (id changed):", start_pages)
    logger.info("Total PDF pages: %s", num_pages)
    logger.info("Document start pages: %s", start_pages)
    return sorted(start_pages)


def split_pdf_by_certificates(pdf_bytes: bytes) -> list[tuple[int, bytes]]:
    """
    Split a PDF into one blob per certificate (each starting at a page containing "REPORT No.").

    Returns a list of (start_page_0based, pdf_bytes) for each certificate.
    """
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as e:
        raise PDFServiceError(f"Failed to read PDF: {e}") from e

    start_pages = find_certificate_start_pages(pdf_bytes)
    total_pages = len(reader.pages)
    split_pdfs: list[tuple[int, bytes]] = []

    for i in range(len(start_pages)):
        start = start_pages[i]
        end = start_pages[i + 1] if i + 1 < len(start_pages) else total_pages
        writer = PdfWriter()
        for page_num in range(start, end):
            writer.add_page(reader.pages[page_num])
        output = BytesIO()
        writer.write(output)
        split_pdfs.append((start, output.getvalue()))

    print("Total split certificates:", len(split_pdfs))
    logger.info("Total split certificates: %s", len(split_pdfs))
    return split_pdfs


def split_pdf_by_pages(pdf_bytes: bytes) -> list[tuple[int, bytes]]:
    """
    Split a PDF into one blob per page. Use when identifier-based split returns 1 chunk
    but we know from OCR text that multiple certificates exist (e.g. Textract sees multiple REPORT No.).
    Returns list of (page_index_0based, pdf_bytes) for each page.
    """
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as e:
        raise PDFServiceError(f"Failed to read PDF: {e}") from e

    result: list[tuple[int, bytes]] = []
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        output = BytesIO()
        writer.write(output)
        result.append((i, output.getvalue()))
    logger.info("Split PDF by pages: %s pages", len(result))
    return result
