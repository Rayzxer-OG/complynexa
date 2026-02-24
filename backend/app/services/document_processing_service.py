"""Document processing: upload to S3, split PDF by REPORT No., extract certificates."""

import logging
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.certificate import Certificate
from app.models.document import Document
from app.services.certificate_name_service import generate_certificate_name
from app.services.date_extraction_service import (
    extract_certificate_name,
    extract_issue_and_expiry,
    extract_report_number,
)
from app.services.llm_extraction_service import (
    detect_document_structure_llm,
    extract_certificate_data_llm_with_dates,
)
from app.services.pdf_service import PDFServiceError, split_pdf_by_certificates, split_pdf_by_pages
from app.services.processing_job_store import set_job, update_job
from app.services.s3_service import (
    S3ServiceError,
    upload_certificate_pdf_to_s3,
    upload_document_to_s3,
)
from app.services.textract_service import TextractError, extract_text_from_pdf_bytes

logger = logging.getLogger(__name__)


def normalize_certificate_name(name: str | None) -> str | None:
    """Normalize certificate name for consistent display (e.g. dashboard)."""
    if name is None or not name.strip():
        return name
    n = name.lower()
    if "power press" in n:
        return "Examination of Power Press and Safety Devices"
    if "pressure vessel" in n:
        return "Report of Examination of Pressure Vessel"
    if "lifting machine" in n:
        return "Examination of Lifting Machines"
    if "insurance" in n:
        return "Insurance Policy Certificate"
    return name.title()


def _save_certificate(
    db: Session,
    job_id: UUID,
    document_id: UUID,
    user_id: UUID,
    extracted_text: str | None,
    pdf_bytes: bytes,
    page_number: int,
    index_for_error: int,
    sequence_number: int = 1,
    source_document_name: str | None = None,
) -> None:
    """Run LLM + regex fallback, upload PDF to S3, create Certificate and add to db."""
    issue_date = None
    expiry_date = None
    report_number = None
    certificate_name = None
    if extracted_text:
        llm_data = extract_certificate_data_llm_with_dates(extracted_text)
        report_number = llm_data.get("report_number")
        certificate_name = llm_data.get("certificate_name")
        issue_date = llm_data.get("issue_date")
        expiry_date = llm_data.get("expiry_date")
        print("LLM extracted:")
        print("  report_number:", report_number)
        print("  certificate_name:", certificate_name)
        print("  issue_date:", issue_date)
        print("  expiry_date:", expiry_date)
        logger.info(
            "LLM extracted: report_number=%s, issue_date=%s, expiry_date=%s",
            report_number,
            issue_date,
            expiry_date,
        )
        if expiry_date is None or issue_date is None:
            dates = extract_issue_and_expiry(extracted_text)
            if issue_date is None:
                issue_date = dates.issue_date
            if expiry_date is None:
                expiry_date = dates.expiry_date
        if report_number is None:
            report_number = extract_report_number(extracted_text)
        if not certificate_name:
            certificate_name = generate_certificate_name(extracted_text)
        if not certificate_name:
            certificate_name = extract_certificate_name(extracted_text)
        certificate_name = certificate_name or report_number
        certificate_name = normalize_certificate_name(certificate_name)

    cert_id = uuid4()
    s3_key = upload_certificate_pdf_to_s3(
        user_id=user_id,
        document_id=document_id,
        certificate_id=cert_id,
        body=pdf_bytes,
    )
    cert = Certificate(
        id=cert_id,
        document_id=document_id,
        user_id=user_id,
        report_number=report_number,
        certificate_name=certificate_name,
        issue_date=issue_date,
        expiry_date=expiry_date,
        page_number=page_number,
        sequence_number=sequence_number,
        source_document_name=source_document_name,
        split_pdf_s3_key=s3_key,
        extracted_text=extracted_text,
    )
    db.add(cert)


def run_processing_pipeline(
    job_id: UUID,
    document_id: UUID,
    user_id: UUID,
    temp_file_path: str,
) -> None:
    """
    Background pipeline: split PDF, extract text per certificate, extract dates, upload to S3, save certificates.
    """
    update_job(
        job_id,
        status="processing",
        progress=10,
        current_step="Splitting PDF into documents...",
        current_page=0,
        total_pages=0,
        total_certificates=0,
    )

    try:
        pdf_bytes = Path(temp_file_path).read_bytes()

        update_job(
            job_id,
            progress=12,
            current_step="Extracting full document text (Textract)...",
        )
        full_text: str | None = None
        try:
            full_text = extract_text_from_pdf_bytes(pdf_bytes)
        except TextractError as e:
            logger.warning("Textract failed on full PDF: %s", e)

        report_no_count = (full_text or "").upper().count("REPORT NO.")
        if full_text:
            print("REPORT NO. count in full text (Textract):", report_no_count)
            logger.info("REPORT NO. count in full text: %s", report_no_count)

        update_job(
            job_id,
            progress=14,
            current_step="Analyzing document structure (LLM)...",
        )
        structure = detect_document_structure_llm(full_text or "")
        document_type = structure.get("document_type") or "single_certificate"
        print("Document type:", structure.get("document_type"))
        print("Certificate count detected:", structure.get("certificate_count"))
        logger.info(
            "LLM structure: document_type=%s, certificate_count=%s",
            document_type,
            structure.get("certificate_count"),
        )

        if report_no_count >= 2:
            document_type = "multi_certificate"
            print("Textract found", report_no_count, "REPORT NO.; treating as multi_certificate")
            logger.info("Textract found %s REPORT NO.; forcing multi_certificate", report_no_count)

        chunks = []
        if document_type == "multi_certificate":
            chunks = split_pdf_by_certificates(pdf_bytes)
            if len(chunks) == 1 and report_no_count >= 2:
                chunks = split_pdf_by_pages(pdf_bytes)
                print("Identifier split returned 1 chunk; using page-by-page split:", len(chunks), "pages")
                logger.info("Fallback: split by pages, %s chunks", len(chunks))
        elif document_type == "single_certificate":
            try:
                preview = split_pdf_by_certificates(pdf_bytes)
                if len(preview) > 1:
                    document_type = "multi_certificate"
                    chunks = preview
                    print("Fallback: PDF splits into", len(chunks), "chunks; treating as multi_certificate")
                    logger.info("Fallback: split_pdf_by_certificates returned %s chunks; using multi_certificate", len(chunks))
            except PDFServiceError:
                pass

        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            source_document_name = doc.filename if doc else None
            if document_type == "multi_certificate":
                update_job(
                    job_id,
                    progress=15,
                    total_certificates=0,
                    current_step="Multi-certificate report detected. Splitting...",
                )
                total = len(chunks)
                print("Split certificates:", len(chunks))
                update_job(job_id, total_certificates=total)
                for i, (page_number_0based, cert_pdf_bytes) in enumerate(chunks):
                    print("Processing certificate {} of {}".format(i + 1, total))
                    update_job(
                        job_id,
                        progress=15 + int((i + 1) / total * 75),
                        current_step="Document {} of {}: AWS Textract (OCR) extracting text...".format(i + 1, total),
                        current_page=page_number_0based + 1,
                        total_pages=total,
                    )
                    extracted_text = None
                    try:
                        extracted_text = extract_text_from_pdf_bytes(cert_pdf_bytes)
                    except TextractError as e:
                        logger.warning("Textract failed for certificate %s: %s", i + 1, e)
                    update_job(
                        job_id,
                        current_step="Document {} of {}: AI analyzing dates & naming...".format(i + 1, total),
                    )
                    _save_certificate(
                        db=db,
                        job_id=job_id,
                        document_id=document_id,
                        user_id=user_id,
                        extracted_text=extracted_text,
                        pdf_bytes=cert_pdf_bytes,
                        page_number=page_number_0based + 1,
                        index_for_error=i + 1,
                        sequence_number=i + 1,
                        source_document_name=source_document_name,
                    )
                total_saved = total
            else:
                update_job(
                    job_id,
                    progress=20,
                    total_certificates=1,
                    current_step="Single document detected. AI analyzing full text...",
                )
                _save_certificate(
                    db=db,
                    job_id=job_id,
                    document_id=document_id,
                    user_id=user_id,
                    extracted_text=full_text,
                    pdf_bytes=pdf_bytes,
                    page_number=1,
                    index_for_error=1,
                    sequence_number=1,
                    source_document_name=source_document_name,
                )
                total_saved = 1

            certs_list = (
                db.query(Certificate)
                .filter(Certificate.document_id == document_id)
                .order_by(Certificate.sequence_number.asc())
                .all()
            )
            if doc:
                if certs_list:
                    first_name = (certs_list[0].certificate_name or "").strip()
                    if len(certs_list) == 1:
                        doc.document_name = first_name or None
                    else:
                        doc.document_name = (first_name + " Report") if first_name else None
                if not doc.document_name:
                    doc.document_name = "Compliance Document"

            db.commit()
        finally:
            db.close()

        update_job(
            job_id,
            status="completed",
            progress=100,
            current_step="Done. Documents saved (AWS Textract OCR + AI extraction).",
            total_certificates=total_saved,
        )
    except PDFServiceError as e:
        logger.exception("PDF split failed: %s", e)
        update_job(job_id, status="failed", progress=0, error=str(e))
    except Exception as e:
        logger.exception("Processing failed: %s", e)
        update_job(job_id, status="failed", progress=0, error=str(e))
    finally:
        path = Path(temp_file_path)
        if path.exists():
            try:
                path.unlink()
            except OSError as e:
                logger.warning("Failed to delete temp file %s: %s", temp_file_path, e)
