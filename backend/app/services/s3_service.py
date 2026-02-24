"""S3 service for secure document and certificate storage (private bucket, signed URLs)."""

import logging
from uuid import UUID

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Default signed URL expiry (1 hour)
SIGNED_URL_EXPIRY_SECONDS = 3600


class S3ServiceError(Exception):
    """Raised when S3 operations fail."""

    pass


def _get_client():
    settings = get_settings()
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    return boto3.client("s3", **kwargs)


def _get_bucket() -> str:
    bucket = (get_settings().aws_s3_bucket or "").strip()
    if not bucket:
        raise S3ServiceError("AWS_S3_BUCKET is not set. Configure it in .env for document storage.")
    return bucket


def upload_document_to_s3(
    *,
    user_id: UUID,
    document_id: UUID,
    original_filename: str,
    body: bytes,
    content_type: str = "application/pdf",
    as_pdf_key: bool = True,
) -> str:
    """
    Upload a document to S3. Returns the S3 key (stored for later signed URL generation).

    Key pattern: documents/{user_id}/{document_id}/{safe_filename}
    When as_pdf_key is True (default), the stored key always ends with .pdf.
    When as_pdf_key is False, the original extension is kept (for storing originals).
    """
    bucket = _get_bucket()
    safe_name = original_filename.replace(" ", "_").strip() or "document.pdf"
    if as_pdf_key and not safe_name.lower().endswith(".pdf"):
        safe_name += ".pdf"
    key = f"documents/{user_id}/{document_id}/{safe_name}"
    try:
        client = _get_client()
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
    except (BotoCoreError, ClientError) as e:
        logger.exception("S3 upload failed for key %s", key)
        raise S3ServiceError(f"Failed to upload document to S3: {e}") from e
    return key


def upload_certificate_pdf_to_s3(
    *,
    user_id: UUID,
    document_id: UUID,
    certificate_id: UUID,
    body: bytes,
) -> str:
    """
    Upload a split certificate PDF to S3. Returns the S3 key.
    Key pattern: certificates/{user_id}/{document_id}/{certificate_id}.pdf
    """
    bucket = _get_bucket()
    key = f"certificates/{user_id}/{document_id}/{certificate_id}.pdf"
    try:
        client = _get_client()
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType="application/pdf",
        )
    except (BotoCoreError, ClientError) as e:
        logger.exception("S3 upload failed for certificate key %s", key)
        raise S3ServiceError(f"Failed to upload certificate to S3: {e}") from e
    return key


def generate_presigned_url(
    s3_key: str,
    *,
    expires_in: int = SIGNED_URL_EXPIRY_SECONDS,
    response_content_disposition: str | None = None,
) -> str:
    """
    Generate a presigned GET URL for viewing or downloading.

    Use response_content_disposition for download (e.g. 'attachment; filename="cert.pdf"').
    """
    bucket = _get_bucket()
    try:
        client = _get_client()
        params = {
            "Bucket": bucket,
            "Key": s3_key,
        }
        if response_content_disposition:
            params["ResponseContentDisposition"] = response_content_disposition
        url = client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
        )
    except (BotoCoreError, ClientError) as e:
        logger.exception("Failed to generate presigned URL for %s", s3_key)
        raise S3ServiceError(f"Failed to generate signed URL: {e}") from e
    return url


def delete_object(s3_key: str) -> None:
    """Delete an object from S3. Ignores 404 (object may already be gone)."""
    bucket = _get_bucket()
    try:
        client = _get_client()
        client.delete_object(Bucket=bucket, Key=s3_key)
    except (BotoCoreError, ClientError) as e:
        logger.warning("S3 delete failed for key %s: %s", s3_key, e)
        raise S3ServiceError(f"Failed to delete object from S3: {e}") from e
