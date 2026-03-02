"""
Email service: all reminder emails sent via Resend (notifications@complynexa.com).
Single centralized send_email used by scheduler and reminder logic.
"""

import logging
from datetime import date

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document
from app.models.reminder_log import ReminderLog
from app.models.user import User

logger = logging.getLogger(__name__)

# Sender: FROM_NAME <FROM_EMAIL> e.g. Complynexa <notifications@complynexa.com>
# Loaded from .env via get_settings(): RESEND_API_KEY, FROM_EMAIL, FROM_NAME


def send_email(to_email: str, subject: str, html_content: str) -> tuple[bool, str | object]:
    """
    Send an email via Resend API. Single centralized function used everywhere.
    Uses RESEND_API_KEY, FROM_EMAIL, FROM_NAME from environment (.env).
    Does not raise; logs errors so the scheduler and app do not crash.
    Returns (True, email_response) if sent successfully, (False, error_message) otherwise.
    """
    settings = get_settings()
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set; skipping email to %s", to_email)
        return False, "RESEND_API_KEY not set"
    from_email = (settings.from_email or "").strip() or "notifications@complynexa.com"
    from_name = (settings.from_name or "").strip() or "Complynexa"
    # Sender format exactly: FROM_NAME <FROM_EMAIL>
    from_header = f"{from_name} <{from_email}>"
    try:
        import resend
        resend.api_key = settings.resend_api_key
        params = {
            "from": from_header,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        email = resend.Emails.send(params)
        logger.info("Resend email sent to %s subject=%s", to_email, subject[:50])
        return True, email
    except Exception as e:
        err_msg = str(e)
        if "getaddrinfo failed" in err_msg or "Failed to resolve" in err_msg or "NameResolutionError" in err_msg:
            friendly = (
                "Network/DNS error: could not reach api.resend.com. "
                "Check internet connection, DNS, firewall, or VPN."
            )
            logger.warning("Resend send_email failed (to=%s): %s", to_email, friendly)
            return False, friendly
        logger.exception("Resend send_email failed (to=%s): %s", to_email, e)
        return False, err_msg


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


def reminder_email_template(document: Document, reminder_type: str = "") -> str:
    """HTML body for document expiry reminder."""
    name = document.document_name or document.filename or "Document"
    expiry_str = _format_expiry_date(document.expiry_date)
    return f"""
    <h2>Document Expiry Reminder</h2>

    <p>Your document <b>{name}</b> is expiring soon.</p>

    <p>Expiry Date: {expiry_str}</p>

    <p>Please renew it before expiry.</p>

    <br>

    <p>
    Regards,<br>
    Complynexa
    </p>
    """


def _reminder_subject(document: Document) -> str:
    """Subject line for document reminder."""
    name = document.document_name or document.filename or "Unnamed document"
    days = _days_remaining(document.expiry_date)
    if days is not None:
        return f"Complynexa: Action required – '{name}' expiring in {days} day{'s' if days != 1 else ''}"
    return f"Complynexa: Document reminder – {name}"


def send_email_reminder(document: Document, db: Session) -> None:
    """
    Send a reminder email for a document expiring soon via Resend, then log it to prevent duplicates.
    ReminderLog is created only after successful send. Failed sends are logged (status=failed) and do not create ReminderLog,
    so duplicate prevention remains intact and the scheduler continues.
    Caller must commit the session after this returns when send succeeded.
    """
    settings = get_settings()
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set; skipping reminder for document %s", document.id)
        return
    user = db.query(User).filter(User.id == document.user_id).first()
    if not user or not (user.email or "").strip():
        logger.warning("No user or email for document %s; skipping reminder", document.id)
        return
    to_email = user.email.strip()
    subject = _reminder_subject(document)
    html_content = reminder_email_template(document, "legacy")
    success, result = send_email(to_email, subject, html_content)
    if success:
        log = ReminderLog(
            document_id=document.id,
            reminder_type="legacy",
            sent_to_email=to_email,
        )
        db.add(log)
    else:
        logger.warning(
            "Reminder email status=failed for document_id=%s to=%s error=%s",
            document.id,
            to_email,
            result,
        )
