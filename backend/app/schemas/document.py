"""Document schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, computed_field


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
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def status(self) -> str | None:
        """Computed status: Expired | Expiring Soon | Active, or None if no expiry_date."""
        return _document_status(self.expiry_date, self.reminder_days)

    model_config = {"from_attributes": True}


class DocumentUpdate(BaseModel):
    """Schema for partial document update (PATCH)."""

    document_name: str | None = None
    expiry_date: date | None = None
    category: str | None = None
    reminder_days: int | None = None
