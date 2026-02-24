"""Processing job status schema."""

from pydantic import BaseModel


class ProcessingStatusResponse(BaseModel):
    """Processing job status for polling."""

    job_id: str
    document_id: str
    status: str  # pending | uploading | processing | extracting | saving | completed | failed
    progress: int
    current_step: str
    current_page: int
    total_pages: int
    total_certificates: int
    error: str | None = None
