"""Certificate schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, computed_field


def _certificate_status(expiry_date: date | None) -> str:
    """Valid | Expiring Soon | Expired."""
    if expiry_date is None:
        return "Valid"
    today = date.today()
    if expiry_date < today:
        return "Expired"
    days_left = (expiry_date - today).days
    if days_left <= 30:
        return "Expiring Soon"
    return "Valid"


class CertificateResponse(BaseModel):
    """Certificate in API responses."""

    id: UUID
    document_id: UUID
    user_id: UUID
    report_number: str | None
    certificate_name: str | None
    issue_date: date | None
    expiry_date: date | None
    page_number: int | None
    extracted_text: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CertificateWithUrlsResponse(CertificateResponse):
    """Certificate with view and download signed URLs (short-lived)."""

    view_url: str | None = None
    download_url: str | None = None


class CertificateListResponse(BaseModel):
    """Certificate list item (for cards) with status and URLs."""

    id: UUID
    document_id: UUID
    report_number: str | None
    certificate_name: str | None
    issue_date: date | None
    expiry_date: date | None
    page_number: int | None
    created_at: datetime
    source_document_name: str | None = None
    view_url: str | None = None
    download_url: str | None = None
    status: str = "Valid"  # Valid | Expiring Soon | Expired; set when building response

    model_config = {"from_attributes": True}


class CertificateListPaginatedResponse(BaseModel):
    """Paginated list of certificates."""

    items: list[CertificateListResponse]
    total: int
    skip: int
    limit: int
