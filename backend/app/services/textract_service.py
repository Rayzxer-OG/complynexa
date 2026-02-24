"""AWS Textract service for document text extraction (S3 + async API)."""

import logging
import time
from pathlib import Path
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 2
MAX_WAIT_SEC = 300


class TextractError(Exception):
    """Raised when Textract extraction fails."""

    pass


def _get_settings():
    return get_settings()


def _boto_kwargs():
    s = _get_settings()
    kwargs: dict = {"region_name": s.aws_region}
    if s.aws_access_key_id and s.aws_secret_access_key:
        kwargs["aws_access_key_id"] = s.aws_access_key_id
        kwargs["aws_secret_access_key"] = s.aws_secret_access_key
    return kwargs


def upload_file_to_s3(file_path: str) -> str:
    """
    Upload file to the configured S3 bucket.

    Uses AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_S3_BUCKET
    from environment.

    Args:
        file_path: Local path to the file.

    Returns:
        S3 key (object key) of the uploaded file.

    Raises:
        TextractError: If bucket not configured, file missing, or upload fails.
    """
    path = Path(file_path)
    if not path.exists():
        raise TextractError(f"File not found: {file_path}")

    settings = _get_settings()
    bucket = (settings.aws_s3_bucket or "").strip()
    if not bucket:
        raise TextractError(
            "AWS_S3_BUCKET is not set. Set it in .env to use Textract extraction."
        )

    suffix = path.suffix.lower() or ".pdf"
    s3_key = f"textract-temp/{uuid4().hex}{suffix}"

    try:
        with open(path, "rb") as f:
            body = f.read()
    except OSError as e:
        raise TextractError(f"Failed to read file {file_path}: {e}") from e

    content_type = "application/pdf" if suffix == ".pdf" else "application/octet-stream"
    try:
        s3 = boto3.client("s3", **_boto_kwargs())
        s3.put_object(Bucket=bucket, Key=s3_key, Body=body, ContentType=content_type)
    except (BotoCoreError, ClientError) as e:
        logger.exception("S3 upload failed for %s", file_path)
        raise TextractError(f"Failed to upload to S3: {e}") from e

    return s3_key


def upload_pdf_bytes_to_s3(pdf_bytes: bytes) -> str:
    """
    Upload PDF bytes to S3 temp for Textract. Returns S3 key.
    Caller must delete the object after extraction.
    """
    settings = _get_settings()
    bucket = (settings.aws_s3_bucket or "").strip()
    if not bucket:
        raise TextractError("AWS_S3_BUCKET is not set.")
    s3_key = f"textract-temp/{uuid4().hex}.pdf"
    try:
        s3 = boto3.client("s3", **_boto_kwargs())
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
    except (BotoCoreError, ClientError) as e:
        logger.exception("S3 upload failed for bytes")
        raise TextractError(f"Failed to upload to S3: {e}") from e
    return s3_key


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extract text from in-memory PDF bytes using S3 + async Textract.
    Uploads to temp S3 key, runs Textract, returns text, deletes temp object.
    """
    settings = _get_settings()
    bucket = (settings.aws_s3_bucket or "").strip()
    if not bucket:
        raise TextractError("AWS_S3_BUCKET is not set.")
    s3_key = upload_pdf_bytes_to_s3(pdf_bytes)
    s3 = boto3.client("s3", **_boto_kwargs())
    textract = boto3.client("textract", **_boto_kwargs())
    try:
        start_resp = textract.start_document_text_detection(
            DocumentLocation={"S3Object": {"Bucket": bucket, "Name": s3_key}}
        )
    except (BotoCoreError, ClientError) as e:
        try:
            s3.delete_object(Bucket=bucket, Key=s3_key)
        except Exception:
            pass
        raise TextractError(f"Textract start failed: {e}") from e

    job_id = start_resp["JobId"]
    all_lines: list[str] = []
    next_token = None
    deadline = time.monotonic() + MAX_WAIT_SEC
    try:
        while time.monotonic() < deadline:
            kwargs = {"JobId": job_id}
            if next_token:
                kwargs["NextToken"] = next_token
            try:
                resp = textract.get_document_text_detection(**kwargs)
            except (BotoCoreError, ClientError) as e:
                raise TextractError(f"Textract get results failed: {e}") from e
            status = resp.get("JobStatus")
            if status == "FAILED":
                raise TextractError("Textract job failed.")
            if status == "SUCCEEDED":
                for block in resp.get("Blocks", []):
                    if block.get("BlockType") == "LINE":
                        t = block.get("Text")
                        if t:
                            all_lines.append(t)
                next_token = resp.get("NextToken")
                if not next_token:
                    break
                time.sleep(0.5)
                continue
            time.sleep(POLL_INTERVAL_SEC)
        else:
            raise TextractError("Textract job timed out.")
    finally:
        try:
            s3.delete_object(Bucket=bucket, Key=s3_key)
        except Exception:
            logger.warning("Failed to delete S3 temp %s", s3_key)
    return "\n".join(all_lines).strip()


def extract_text_async(file_path: str) -> str:
    """
    Extract text using S3 + async Textract (supports multi-page PDFs).

    Steps: upload file to S3, start_document_text_detection, poll
    get_document_text_detection every 2 seconds until SUCCEEDED,
    collect LINE blocks and return joined text. Cleans up S3 object when done.

    Uses AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_S3_BUCKET.

    Args:
        file_path: Local path to the document file.

    Returns:
        Extracted text from all LINE blocks.

    Raises:
        TextractError: On config error, upload failure, or Textract API failure.
    """
    settings = _get_settings()
    bucket = (settings.aws_s3_bucket or "").strip()
    if not bucket:
        raise TextractError(
            "AWS_S3_BUCKET is not set. Set it in .env to use Textract extraction."
        )

    s3_key = upload_file_to_s3(file_path)
    s3 = boto3.client("s3", **_boto_kwargs())
    textract = boto3.client("textract", **_boto_kwargs())

    try:
        start_resp = textract.start_document_text_detection(
            DocumentLocation={"S3Object": {"Bucket": bucket, "Name": s3_key}}
        )
    except (BotoCoreError, ClientError) as e:
        logger.exception("Textract start_document_text_detection failed")
        raise TextractError(f"Textract start failed: {e}") from e

    job_id = start_resp["JobId"]
    all_lines: list[str] = []
    next_token = None
    deadline = time.monotonic() + MAX_WAIT_SEC

    try:
        while time.monotonic() < deadline:
            kwargs: dict = {"JobId": job_id}
            if next_token:
                kwargs["NextToken"] = next_token

            try:
                resp = textract.get_document_text_detection(**kwargs)
            except (BotoCoreError, ClientError) as e:
                logger.exception("Textract get_document_text_detection failed")
                raise TextractError(f"Textract get results failed: {e}") from e

            status = resp.get("JobStatus")
            if status == "FAILED":
                raise TextractError("Textract job failed.")

            if status == "SUCCEEDED":
                for block in resp.get("Blocks", []):
                    if block.get("BlockType") == "LINE":
                        t = block.get("Text")
                        if t:
                            all_lines.append(t)
                next_token = resp.get("NextToken")
                if not next_token:
                    break
                time.sleep(0.5)
                continue

            time.sleep(POLL_INTERVAL_SEC)
        else:
            raise TextractError("Textract job timed out.")
    finally:
        try:
            s3.delete_object(Bucket=bucket, Key=s3_key)
        except Exception:
            logger.warning("Failed to delete S3 object %s", s3_key)

    return "\n".join(all_lines).strip()


def extract_text_from_document(file_path: str) -> str:
    """
    Extract text from a document (single- or multi-page) using S3 and async Textract.

    Delegates to extract_text_async. Uses AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    AWS_REGION, and AWS_S3_BUCKET from environment.

    Args:
        file_path: Path to the document file on disk.

    Returns:
        Extracted text from all LINE blocks, or empty string if none.

    Raises:
        TextractError: On file read, S3, or Textract errors.
    """
    path = Path(file_path)
    if not path.exists():
        raise TextractError(f"File not found: {file_path}")

    text = extract_text_async(file_path)
    return text or ""
