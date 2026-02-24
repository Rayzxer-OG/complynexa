"""Email service for reminders (SMTP)."""

import logging
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document
from app.models.reminder_log import ReminderLog

logger = logging.getLogger(__name__)

BRAND_NAME = "Complyon"


def _format_expiry_date(d: date | None) -> str:
    """Human-readable expiry date, e.g. 'March 15, 2026'."""
    if d is None:
        return "Not specified"
    return d.strftime("%B %d, %Y")


def _days_remaining(expiry_date: date | None) -> int | None:
    """Days until expiry; None if no expiry date."""
    if expiry_date is None:
        return None
    delta = expiry_date - date.today()
    return max(0, delta.days)


def _build_reminder_content(document: Document) -> tuple[str, str]:
    """Build (subject, body) for reminder email. Handles missing fields gracefully."""
    name = document.document_name or document.filename or "Unnamed document"
    category = document.category if document.category else "Not specified"
    expiry = document.expiry_date
    expiry_str = _format_expiry_date(expiry)
    days = _days_remaining(expiry)

    if days is not None:
        subject = f"{BRAND_NAME}: Action required – '{name}' expiring in {days} day{'s' if days != 1 else ''}"
    else:
        subject = f"{BRAND_NAME}: Document reminder – {name}"

    body_lines = [
        f"You are receiving this reminder from {BRAND_NAME}.",
        "",
        "The following document requires your attention:",
        "",
        f"  Document:  {name}",
        f"  Category:  {category}",
        f"  Expiry:    {expiry_str}",
    ]
    if days is not None:
        body_lines.append(f"  Due in:    {days} day{'s' if days != 1 else ''}")
    body_lines.extend([
        "",
        "Please renew or update this document before the expiry date.",
        "",
        f"— {BRAND_NAME} Compliance Tracker",
    ])
    body = "\n".join(body_lines)
    return subject, body


def send_email_reminder(document: Document, db: Session) -> None:
    """
    Send a reminder email for a document expiring soon, then log it to prevent duplicates.

    Uses SMTP settings from environment (SMTP_HOST, SMTP_PORT, SMTP_USER,
    SMTP_PASSWORD, SMTP_FROM, SMTP_TO). If SMTP is not configured, logs a warning
    and still records the reminder in reminder_logs so we do not resend.

    Caller must commit the session after this returns.
    """
    name = document.document_name or document.filename or "Unnamed document"
    settings = get_settings()

    if not all([
        settings.smtp_host,
        settings.smtp_from,
        settings.smtp_to,
    ]):
        logger.warning(
            "SMTP not fully configured (SMTP_HOST, SMTP_FROM, SMTP_TO required); "
            "skipping email for document '%s'",
            name,
        )
        log = ReminderLog(document_id=document.id)
        db.add(log)
        return

    subject, body = _build_reminder_content(document)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = settings.smtp_to
    msg.attach(MIMEText(body, "plain"))

    try:
        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_from, [settings.smtp_to], msg.as_string())
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_from, [settings.smtp_to], msg.as_string())
    except smtplib.SMTPException as e:
        logger.exception("SMTP error sending reminder for document %s: %s", document.id, e)
        raise
    except Exception as e:
        logger.exception("Failed to send reminder email for document %s: %s", document.id, e)
        raise

    log = ReminderLog(document_id=document.id)
    db.add(log)
