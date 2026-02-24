"""In-memory store for document processing job progress (production: use Redis)."""

import threading
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

# In-memory store; keyed by job_id (UUID)
_jobs: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()


@dataclass
class JobProgress:
    """Progress state for a single job."""

    job_id: str
    document_id: str
    status: str  # pending | uploading | processing | extracting | saving | completed | failed
    progress: int  # 0-100
    current_step: str
    current_page: int
    total_pages: int
    total_certificates: int
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "document_id": self.document_id,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "total_certificates": self.total_certificates,
            "error": self.error,
        }


def set_job(job_id: UUID | str, data: dict[str, Any]) -> None:
    with _lock:
        _jobs[str(job_id)] = data


def get_job(job_id: UUID | str) -> dict[str, Any] | None:
    with _lock:
        return _jobs.get(str(job_id))


def update_job(
    job_id: UUID | str,
    *,
    status: str | None = None,
    progress: int | None = None,
    current_step: str | None = None,
    current_page: int | None = None,
    total_pages: int | None = None,
    total_certificates: int | None = None,
    error: str | None = None,
) -> None:
    with _lock:
        j = _jobs.get(str(job_id))
        if not j:
            return
        if status is not None:
            j["status"] = status
        if progress is not None:
            j["progress"] = progress
        if current_step is not None:
            j["current_step"] = current_step
        if current_page is not None:
            j["current_page"] = current_page
        if total_pages is not None:
            j["total_pages"] = total_pages
        if total_certificates is not None:
            j["total_certificates"] = total_certificates
        if error is not None:
            j["error"] = error
