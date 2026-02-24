"""Upload document (multi-certificate PDF) and processing status APIs."""

import logging
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.processing import ProcessingStatusResponse
from app.services.document_processing_service import run_processing_pipeline
from app.services.file_conversion_service import convert_to_pdf
from app.services.processing_job_store import get_job, set_job
from app.services.s3_service import S3ServiceError, upload_document_to_s3

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

SUPPORTED_EXTENSIONS = [
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".tiff",
    ".bmp",
    ".docx",
    ".doc",
    ".xlsx",
    ".xls",
    ".txt",
]


def _validate_upload_filename(filename: str | None) -> None:
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing filename",
        )
    fn = filename.lower()
    if not any(fn.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format",
        )


def _process_one_document(
    *,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    current_user: User,
    db: Session,
) -> dict:
    """Process a single file: validate, convert, upload to S3, create document, start pipeline. Returns dict with filename, job_id, document_id. Raises HTTPException on failure."""
    _validate_upload_filename(file.filename)

    try:
        body = file.file.read()
    except Exception as e:
        logger.exception("Failed to read upload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read file",
        ) from e

    if len(body) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    try:
        pdf_bytes = convert_to_pdf(body, file.filename or "")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    job_id = uuid4()
    document_id = uuid4()
    temp_path = upload_path / f"processing_{job_id.hex}.pdf"
    try:
        temp_path.write_bytes(pdf_bytes)
    except OSError as e:
        logger.exception("Failed to write temp file")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file",
        ) from e

    set_job(
        job_id,
        {
            "job_id": str(job_id),
            "document_id": str(document_id),
            "status": "uploading",
            "progress": 5,
            "current_step": "Uploading...",
            "current_page": 0,
            "total_pages": 0,
            "total_certificates": 0,
            "error": None,
        },
    )

    try:
        upload_document_to_s3(
            user_id=current_user.id,
            document_id=document_id,
            original_filename=file.filename or "original",
            body=body,
            content_type="application/octet-stream",
            as_pdf_key=False,
        )
        s3_key = upload_document_to_s3(
            user_id=current_user.id,
            document_id=document_id,
            original_filename=(Path(file.filename or "document").stem + ".pdf"),
            body=pdf_bytes,
        )
    except S3ServiceError as e:
        set_job(
            job_id,
            {
                "job_id": str(job_id),
                "document_id": str(document_id),
                "status": "failed",
                "progress": 0,
                "current_step": "",
                "current_page": 0,
                "total_pages": 0,
                "total_certificates": 0,
                "error": str(e),
            },
        )
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to upload to storage",
        ) from e

    doc = Document(
        id=document_id,
        user_id=current_user.id,
        filename=file.filename,
        file_path=str(temp_path),
        s3_url=s3_key,
        extracted_text=None,
    )
    db.add(doc)
    db.commit()

    background_tasks.add_task(
        run_processing_pipeline,
        job_id=job_id,
        document_id=document_id,
        user_id=current_user.id,
        temp_file_path=str(temp_path),
    )

    return {
        "filename": file.filename or "document",
        "job_id": str(job_id),
        "document_id": str(document_id),
    }


@router.post("/upload-document")
def upload_document(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile | None = File(None),
    files: list[UploadFile] = File(default=[]),
) -> dict:
    """
    Upload one or more documents. Each file is converted to PDF if needed, stored in S3,
    and processed independently in the background.
    Accepts either a single "file" (backward compatible) or multiple "files".
    Returns success and a list of { filename, job_id, document_id } per file (or error per file).
    """
    file_list: list[UploadFile] = list(files) if files else ([file] if file else [])
    if not file_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file(s) provided. Use 'file' or 'files'.",
        )

    results: list[dict] = []
    for f in file_list:
        try:
            r = _process_one_document(
                background_tasks=background_tasks,
                file=f,
                current_user=current_user,
                db=db,
            )
            results.append(r)
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Failed to process file %s", f.filename)
            results.append({
                "filename": f.filename or "unknown",
                "error": str(e),
            })

    return {
        "success": True,
        "files": results,
    }


@router.post("/upload-locker-document")
def upload_locker_document(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Upload a file to the document locker only. Converts to PDF when needed; stores original and PDF in S3.
    No Textract processing, no Certificate records.
    """
    _validate_upload_filename(file.filename)

    try:
        body = file.file.read()
    except Exception as e:
        logger.exception("Failed to read upload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read file",
        ) from e

    if len(body) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    try:
        pdf_bytes = convert_to_pdf(body, file.filename or "")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    document_id = uuid4()
    try:
        upload_document_to_s3(
            user_id=current_user.id,
            document_id=document_id,
            original_filename=file.filename or "original",
            body=body,
            content_type="application/octet-stream",
            as_pdf_key=False,
        )
        s3_key = upload_document_to_s3(
            user_id=current_user.id,
            document_id=document_id,
            original_filename=(Path(file.filename or "document").stem + ".pdf"),
            body=pdf_bytes,
        )
    except S3ServiceError as e:
        logger.exception("Locker S3 upload failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to upload to storage",
        ) from e

    doc = Document(
        id=document_id,
        user_id=current_user.id,
        filename=file.filename,
        file_path=f"locker:{s3_key}",  # No local file; S3 only
        s3_url=s3_key,
        extracted_text=None,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "s3_url": doc.s3_url,
        "created_at": doc.created_at.isoformat(),
    }


@router.get("/processing-status/{job_id}", response_model=ProcessingStatusResponse)
def get_processing_status(job_id: UUID) -> ProcessingStatusResponse:
    """Get processing job progress (poll from frontend)."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return ProcessingStatusResponse(**job)
