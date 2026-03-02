"""Document API endpoints."""

import logging
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.document import Document
from app.models.unit import Unit
from app.models.user import User
from app.models.user_compliance import UserCompliance
from app.schemas.document import DocumentResponse, DocumentUpdate, OcrExtractResponse
from app.services.ai_extraction_service import extract_compliance_fields, extract_compliance_fields_ocr
from app.services.s3_service import S3ServiceError, generate_presigned_url, get_object_bytes
from app.services.textract_service import TextractError, extract_text_from_document, extract_text_from_pdf_bytes

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    """Upload a document, save to disk, extract text with Textract, and store the record."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing filename",
        )

    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid4().hex}_{file.filename}"
    file_path = upload_path / safe_name

    try:
        with file_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except OSError as e:
        logger.exception("Failed to save upload %s", file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file",
        ) from e

    stored_path_str = str(file_path.resolve())
    extracted_text: str | None = None

    try:
        extracted_text = extract_text_from_document(stored_path_str)
    except TextractError as e:
        logger.warning("Textract extraction failed for %s: %s", file.filename, e)
        # Continue without extracted text; field stays null

    document_name: str | None = None
    expiry_date = None
    category: str | None = None

    if extracted_text:
        fields = extract_compliance_fields(extracted_text)
        document_name = fields.get("document_name")
        category = fields.get("category")
        raw_date = fields.get("expiry_date")
        if raw_date:
            try:
                expiry_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

    doc = Document(
        user_id=current_user.id,
        filename=file.filename,
        file_path=stored_path_str,
        extracted_text=extracted_text or None,
        document_name=document_name,
        expiry_date=expiry_date,
        category=category,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


DocumentStatusFilter = Literal["active", "expiring_soon", "expired"]


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    status: DocumentStatusFilter | None = None,
) -> list[Document]:
    """List documents for the current user with optional pagination and status filter."""
    today = date.today()
    query = db.query(Document).filter(Document.user_id == current_user.id)
    if status is not None:
        query = query.filter(Document.expiry_date.isnot(None))
        if status == "expired":
            query = query.filter(Document.expiry_date < today)
        elif status == "expiring_soon":
            query = query.filter(
                Document.expiry_date >= today,
                text("documents.expiry_date <= current_date + documents.reminder_days"),
            )
        else:  # active
            query = query.filter(
                text("documents.expiry_date > current_date + documents.reminder_days"),
            )
    return query.order_by(Document.id).offset(skip).limit(limit).all()


@router.get("/{document_id}/view-url")
def get_document_view_url(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get a short-lived signed URL to view the document PDF (for locker)."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    if not doc.s3_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no S3 storage",
        )
    try:
        url = generate_presigned_url(doc.s3_url, expires_in=3600)
        return {"url": url}
    except S3ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to generate view URL",
        ) from e


@router.get("/{document_id}/download-url")
def get_document_download_url(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get a short-lived signed URL to download the document PDF (for locker)."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    if not doc.s3_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no S3 storage",
        )
    try:
        url = generate_presigned_url(
            doc.s3_url,
            expires_in=3600,
            response_content_disposition=f'attachment; filename="{doc.filename}"',
        )
        return {"url": url}
    except S3ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to generate download URL",
        ) from e


@router.get("/{document_id}/extract-ocr", response_model=OcrExtractResponse)
def extract_ocr_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Run OCR and AI extraction on a document; return fields for confirmation form. Requires S3 storage."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    if not doc.s3_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no S3 storage; OCR extraction is not available",
        )
    try:
        pdf_bytes = get_object_bytes(doc.s3_url)
    except S3ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to load document for extraction",
        ) from e
    try:
        text = extract_text_from_pdf_bytes(pdf_bytes)
    except TextractError as e:
        logger.warning("Textract failed for document %s: %s", document_id, e)
        return OcrExtractResponse(
            document_name=None,
            license_number=None,
            issuing_authority=None,
            issue_date=None,
            expiry_date=None,
            unit_name=_unit_name_for_document(db, doc),
            category=None,
        )
    fields = extract_compliance_fields_ocr(text)
    # Prefer unit name extracted from document (license company name); fallback to linked unit's name
    unit_name = fields.get("unit_name") or _unit_name_for_document(db, doc)
    return OcrExtractResponse(
        document_name=fields.get("document_name"),
        license_number=fields.get("license_number"),
        issuing_authority=fields.get("issuing_authority"),
        issue_date=fields.get("issue_date"),
        expiry_date=fields.get("expiry_date"),
        unit_name=unit_name,
        category=fields.get("category"),
    )


def _unit_name_for_document(db: Session, doc: Document) -> str | None:
    """Return unit_name for document's unit_id, or None."""
    if not doc.unit_id:
        return None
    unit = db.query(Unit).filter(Unit.id == doc.unit_id).first()
    return unit.unit_name if unit else None


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    """Get a document by ID. Returns 404 if not found or not owned by current user."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return doc


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: UUID,
    body: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    """Update a document by ID. Returns 404 if not found or not owned by current user."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    data = body.model_dump(exclude_unset=True, by_alias=False)
    data.pop("unit_name", None)  # Not stored on Document; unit_id is the source of truth
    for key, value in data.items():
        setattr(doc, key, value)
    db.commit()
    db.refresh(doc)
    # After user confirms OCR data, mark compliance as uploaded so checklist updates.
    if doc.compliance_requirement_id is not None and doc.unit_id is not None:
        db.query(UserCompliance).filter(
            UserCompliance.user_id == current_user.id,
            UserCompliance.unit_id == doc.unit_id,
            UserCompliance.compliance_requirement_id == doc.compliance_requirement_id,
        ).update({UserCompliance.status: "uploaded"}, synchronize_session=False)
        db.commit()
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a document by ID. Returns 404 if not found or not owned by current user."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    if doc.file_path and not doc.file_path.startswith("locker:"):
        file_path = Path(doc.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError as e:
                logger.warning("Failed to delete file %s: %s", doc.file_path, e)
    db.delete(doc)
    db.commit()
