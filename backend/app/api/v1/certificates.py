"""Certificate API endpoints."""

from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.certificate import Certificate
from app.models.document import Document
from app.models.user import User
from app.schemas.certificate import (
    CertificateListPaginatedResponse,
    CertificateListResponse,
    CertificateResponse,
    _certificate_status,
)
from app.services.s3_service import S3ServiceError, delete_object, generate_presigned_url

router = APIRouter()

# Signed URL expiry (1 hour)
URL_EXPIRY = 3600


@router.get("", response_model=CertificateListPaginatedResponse)
def list_certificates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    status_filter: str | None = None,  # Valid | Expiring Soon | Expired
) -> CertificateListPaginatedResponse:
    """List certificates for the current user (for document locker / dashboard cards)."""
    query = db.query(Certificate).filter(Certificate.user_id == current_user.id)
    if status_filter:
        today = date.today()
        if status_filter == "Expired":
            query = query.filter(Certificate.expiry_date < today)
        elif status_filter == "Expiring Soon":
            query = query.filter(
                Certificate.expiry_date >= today,
                Certificate.expiry_date <= today + timedelta(days=30),
            )
        elif status_filter == "Valid":
            query = query.filter(
                (Certificate.expiry_date.is_(None))
                | (Certificate.expiry_date > today + timedelta(days=30))
            )
    total = query.count()
    # Newest uploads first; within each upload preserve PDF sequence
    certs = (
        query.order_by(
            Certificate.created_at.desc(),
            Certificate.sequence_number.asc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    result = []
    for c in certs:
        view_url = None
        download_url = None
        try:
            view_url = generate_presigned_url(c.split_pdf_s3_key, expires_in=URL_EXPIRY)
            download_url = generate_presigned_url(
                c.split_pdf_s3_key,
                expires_in=URL_EXPIRY,
                response_content_disposition=f'attachment; filename="certificate-{c.id}.pdf"',
            )
        except S3ServiceError:
            pass
        result.append(
            CertificateListResponse(
                id=c.id,
                document_id=c.document_id,
                report_number=c.report_number,
                certificate_name=c.certificate_name,
                issue_date=c.issue_date,
                expiry_date=c.expiry_date,
                page_number=c.page_number,
                created_at=c.created_at,
                source_document_name=c.source_document_name,
                view_url=view_url,
                download_url=download_url,
                status=_certificate_status(c.expiry_date),
            )
        )
    return CertificateListPaginatedResponse(items=result, total=total, skip=skip, limit=limit)


def _cert_list_response(c: Certificate) -> CertificateListResponse:
    """Build CertificateListResponse with presigned URLs and status."""
    view_url = None
    download_url = None
    try:
        view_url = generate_presigned_url(c.split_pdf_s3_key, expires_in=URL_EXPIRY)
        download_url = generate_presigned_url(
            c.split_pdf_s3_key,
            expires_in=URL_EXPIRY,
            response_content_disposition=f'attachment; filename="certificate-{c.id}.pdf"',
        )
    except S3ServiceError:
        pass
    return CertificateListResponse(
        id=c.id,
        document_id=c.document_id,
        report_number=c.report_number,
        certificate_name=c.certificate_name,
        issue_date=c.issue_date,
        expiry_date=c.expiry_date,
        page_number=c.page_number,
        created_at=c.created_at,
        source_document_name=c.source_document_name,
        view_url=view_url,
        download_url=download_url,
        status=_certificate_status(c.expiry_date),
    )


@router.get("/grouped")
def list_certificates_grouped(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """
    List certificates grouped by source document. Documents ordered by created_at desc,
    certificates within each document by sequence_number asc.
    """
    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    result = []
    for doc in documents:
        certs = (
            db.query(Certificate)
            .filter(Certificate.document_id == doc.id)
            .order_by(Certificate.sequence_number.asc())
            .all()
        )
        result.append({
            "document_id": str(doc.id),
            "file_name": doc.filename,
            "document_name": doc.document_name,
            "upload_date": doc.created_at.isoformat() if doc.created_at else None,
            "certificates": [_cert_list_response(c) for c in certs],
        })
    return result


class BulkDeleteRequest(BaseModel):
    certificate_ids: list[UUID]


@router.post("/bulk-delete")
def bulk_delete_certificates(
    body: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete multiple certificates and their S3 objects. Only certificates owned by the current user are deleted."""
    if not body.certificate_ids:
        return {"deleted": 0}
    certs = (
        db.query(Certificate)
        .filter(
            Certificate.id.in_(body.certificate_ids),
            Certificate.user_id == current_user.id,
        )
        .all()
    )
    for cert in certs:
        if cert.split_pdf_s3_key:
            try:
                delete_object(cert.split_pdf_s3_key)
            except S3ServiceError:
                pass
        db.delete(cert)
    db.commit()
    return {"deleted": len(certs)}


@router.get("/{certificate_id}", response_model=CertificateResponse)
def get_certificate(
    certificate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Certificate:
    """Get a certificate by ID."""
    cert = (
        db.query(Certificate)
        .filter(Certificate.id == certificate_id, Certificate.user_id == current_user.id)
        .first()
    )
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )
    return cert


@router.get("/{certificate_id}/view-url")
def get_certificate_view_url(
    certificate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get a short-lived signed URL to view the certificate PDF."""
    cert = (
        db.query(Certificate)
        .filter(Certificate.id == certificate_id, Certificate.user_id == current_user.id)
        .first()
    )
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )
    try:
        url = generate_presigned_url(cert.split_pdf_s3_key, expires_in=URL_EXPIRY)
        return {"url": url}
    except S3ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to generate view URL",
        ) from e


@router.get("/{certificate_id}/download-url")
def get_certificate_download_url(
    certificate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get a short-lived signed URL to download the certificate PDF."""
    cert = (
        db.query(Certificate)
        .filter(Certificate.id == certificate_id, Certificate.user_id == current_user.id)
        .first()
    )
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )
    try:
        url = generate_presigned_url(
            cert.split_pdf_s3_key,
            expires_in=URL_EXPIRY,
            response_content_disposition=f'attachment; filename="certificate-{cert.id}.pdf"',
        )
        return {"url": url}
    except S3ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to generate download URL",
        ) from e


@router.delete("/{certificate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certificate(
    certificate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a certificate and its S3 object. Only the owner can delete."""
    cert = (
        db.query(Certificate)
        .filter(Certificate.id == certificate_id, Certificate.user_id == current_user.id)
        .first()
    )
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )
    if cert.split_pdf_s3_key:
        try:
            delete_object(cert.split_pdf_s3_key)
        except S3ServiceError:
            pass
    db.delete(cert)
    db.commit()
