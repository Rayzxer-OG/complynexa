"""Document schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


def _document_status(expiry_date: date | None, reminder_days: int) -> str | None:
    """Compute status from expiry_date and reminder_days."""
    if expiry_date is None:
        return None
    today = date.today()
    if expiry_date < today:
        return "Expired"
    days_left = (expiry_date - today).days
    if days_left <= reminder_days:
        return "Expiring Soon"
    return "Active"


class DocumentResponse(BaseModel):
    """Schema for document in API responses."""

    id: UUID
    filename: str
    file_path: str
    s3_url: str | None = None
    extracted_text: str | None = None
    document_name: str | None = None
    expiry_date: date | None = None
    category: str | None = None
    reminder_days: int = 30
    license_number: str | None = None
    issuing_authority: str | None = None
    issue_date: date | None = None
    document_file_reference: str | None = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def status(self) -> str | None:
        """Computed status: Expired | Expiring Soon | Active, or None if no expiry_date."""
        return _document_status(self.expiry_date, self.reminder_days)

    model_config = {"from_attributes": True}


class DocumentUpdate(BaseModel):
    """Schema for partial document update (PATCH). Used for OCR confirmation save."""

    model_config = ConfigDict(populate_by_name=True)

    document_name: str | None = None
    expiry_date: date | None = None
    category: str | None = None
    reminder_days: int | None = None
    unit_id: UUID | None = None
    compliance_requirement_id: UUID | None = Field(None, alias="compliance_id")
    license_number: str | None = None
    issuing_authority: str | None = None
    issue_date: date | None = None
    unit_name: str | None = None  # Accepted for request; not stored (use unit_id)
    document_file_reference: str | None = None


class OcrExtractResponse(BaseModel):
    """Schema for OCR extraction result (confirmation form)."""

    document_name: str | None = None
    license_number: str | None = None
    issuing_authority: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    unit_name: str | None = None
    category: str | None = None
