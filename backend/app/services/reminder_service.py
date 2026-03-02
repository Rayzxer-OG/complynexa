"""Compliance reminder: documents expiring soon (legacy), certificate expiry reminders (Resend), and compliance expiry reminders."""

import logging
from datetime import date

from sqlalchemy import cast, text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.types import Date

from app.models.certificate import Certificate
from app.models.compliance_escalation_log import ComplianceEscalationLog
from app.models.compliance_reminder import ComplianceReminder
from app.models.compliance_requirement import ComplianceRequirement
from app.models.document import Document
from app.models.reminder_log import ReminderLog
from app.models.unit_escalation_contact import UnitEscalationContact
from app.models.user import User

logger = logging.getLogger(__name__)

# Compliance reminder trigger days (days_remaining) and their reminder_type
# 30, 15 → Level 1; 7, 3 → Level 2; on expiry → Level 3
COMPLIANCE_REMINDER_TRIGGERS = {
    30: "30_day",
    15: "15_day",
    7: "7_day",
    3: "3_day",
}

# Map days_remaining to escalation level for multi-level escalation
def _days_remaining_to_escalation_level(days_remaining: int) -> int:
    """Return escalation level 1, 2, or 3 from days until expiry."""
    if days_remaining >= 15:
        return 1
    if days_remaining >= 3:
        return 2
    return 3

# Certificate reminder schedule: days before/after expiry to send
CERT_REMINDER_DAYS = (60, 30, 15, 7, 3, 1, 0, -3)
DASHBOARD_LINK = "https://complynexa.com/dashboard"


def _certificate_reminder_trigger_days() -> set[int]:
    """Days remaining that trigger a reminder: 60, 30, 15, 7, 3, 1, 0, -3, then weekly after expiry."""
    out = set(CERT_REMINDER_DAYS)
    # Weekly after expiry: -7, -14, -21, -28 (up to 4 weeks)
    for w in range(1, 5):
        out.add(-7 * w)
    return out


def generate_email_content(certificate: Certificate, user: User, days_remaining: int) -> tuple[str, str]:
    """Return (subject, html_body) for certificate expiry reminder."""
    cert_name = certificate.certificate_name or certificate.report_number or "Certificate"
    expiry = certificate.expiry_date
    expiry_str = expiry.strftime("%B %d, %Y") if expiry else "N/A"
    user_name = user.full_name or user.email or "User"

    if days_remaining > 1:
        subject = f"Reminder: {cert_name} expires on {expiry_str}"
    elif days_remaining >= 0:
        subject = f"URGENT: {cert_name} expires in {days_remaining} day(s)"
    else:
        subject = f"NON-COMPLIANT: {cert_name} has expired"

    days_text = f"{days_remaining} days" if days_remaining != 1 else "1 day"
    if days_remaining == 0:
        days_text = "today"
    elif days_remaining < 0:
        days_text = f"{abs(days_remaining)} days ago"

    html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: sans-serif; line-height: 1.5;">
  <p>Hello {user_name},</p>
  <p>This is a compliance certificate expiry reminder from ComplyNexa.</p>
  <ul>
    <li><strong>Certificate:</strong> {cert_name}</li>
    <li><strong>Expiry date:</strong> {expiry_str}</li>
    <li><strong>Days remaining:</strong> {days_text}</li>
  </ul>
  <p>View and manage your certificates in the dashboard:</p>
  <p><a href="{DASHBOARD_LINK}">{DASHBOARD_LINK}</a></p>
  <p>— ComplyNexa</p>
</body>
</html>
"""
    return subject, html_body.strip()


def check_and_send_certificate_reminders(db: Session) -> None:
    """
    Find certificates with expiry_date set whose days_remaining matches the reminder schedule.
    Send one reminder per certificate per day (last_reminder_sent prevents duplicates).
    """
    from app.services.email_service import send_email

    today = date.today()
    trigger_days = _certificate_reminder_trigger_days()
    certificates = (
        db.query(Certificate)
        .filter(Certificate.expiry_date.isnot(None))
        .all()
    )
    for cert in certificates:
        expiry = cert.expiry_date
        if not expiry:
            continue
        days_remaining = (expiry - today).days
        if days_remaining not in trigger_days:
            continue
        if cert.last_reminder_sent == today:
            continue
        user = db.query(User).filter(User.id == cert.user_id).first()
        if not user or not user.email:
            continue
        subject, html_body = generate_email_content(cert, user, days_remaining)
        success, _ = send_email(user.email, subject, html_body)
        if not success:
            continue
        cert.last_reminder_sent = today
        db.commit()
        logger.info(
            "[REMINDER SENT] certificate_id=%s user_email=%s days_remaining=%s",
            cert.id,
            user.email,
            days_remaining,
        )


def _compliance_reminder_email_subject(compliance_name: str) -> str:
    """Subject for compliance expiry reminder."""
    return f"Compliance Expiry Reminder – {compliance_name}"


def _compliance_reminder_email_body(compliance_name: str, expiry_date: str, days_remaining: int) -> str:
    """HTML body for compliance expiry reminder."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: sans-serif; line-height: 1.6;">
<p>Your compliance document:</p>
<p><strong>{compliance_name}</strong></p>
<p>will expire on:</p>
<p><strong>{expiry_date}</strong></p>
<p>Days remaining: <strong>{days_remaining}</strong></p>
<p>Please upload renewed document.</p>
<p>— Complynexa Team</p>
</body>
</html>"""


def _send_escalation_for_doc(
    db: Session,
    doc: Document,
    compliance_name: str,
    expiry_date_str: str,
    days_remaining: int,
    escalation_level: int,
    today: date,
    send_email_fn,
) -> None:
    """Send escalation emails to unit contacts matching level and trigger_days; log for expired daily."""
    contacts = (
        db.query(UnitEscalationContact)
        .filter(
            UnitEscalationContact.unit_id == doc.unit_id,
            UnitEscalationContact.level == escalation_level,
        )
        .all()
    )
    for contact in contacts:
        trigger_days = contact.escalation_trigger_days
        if trigger_days is None:
            continue
        if days_remaining > 0:
            match = trigger_days == days_remaining
        else:
            match = trigger_days == 0
        if not match:
            continue
        if not contact.email or contact.email.strip() == "":
            continue
        esc_subject = _compliance_reminder_email_subject(compliance_name)
        esc_body = _compliance_reminder_email_body(
            compliance_name, expiry_date_str, days_remaining
        )
        esc_success, _ = send_email_fn(contact.email.strip(), esc_subject, esc_body)
        if esc_success:
            if days_remaining < 0:
                db.add(
                    ComplianceEscalationLog(
                        document_id=doc.id,
                        escalation_level=contact.level,
                        sent_to_email=contact.email.strip(),
                    )
                )
            db.commit()
            logger.info(
                "[COMPLIANCE ESCALATION SENT] document_id=%s contact_email=%s level=%s escalation_trigger_days=%s",
                str(doc.id),
                contact.email,
                contact.level,
                contact.escalation_trigger_days,
            )
        else:
            logger.warning("Compliance escalation email failed for %s", contact.email)


def check_and_send_compliance_reminders(db: Session) -> list[dict]:
    """
    Find documents with expiry_date set whose days_remaining matches 30, 15, 7, 3 or expired.
    Multi-level escalation: 30/15 days → Level 1, 7/3 days → Level 2, on expiry → Level 3.
    If expired, continue daily escalation to Level 3 until resolved (one send per day per document).
    """
    from app.services.email_service import send_email

    today = date.today()
    documents = (
        db.query(Document)
        .options(joinedload(Document.user), joinedload(Document.compliance_requirement))
        .filter(Document.expiry_date.isnot(None))
        .all()
    )
    reminders: list[dict] = []
    for doc in documents:
        if doc.expiry_date is None:
            continue
        days_remaining = (doc.expiry_date - today).days
        if days_remaining in COMPLIANCE_REMINDER_TRIGGERS:
            reminder_type = COMPLIANCE_REMINDER_TRIGGERS[days_remaining]
        elif days_remaining < 0:
            reminder_type = "expired"
        else:
            continue
        compliance_name = (
            doc.compliance_requirement.compliance_name
            if doc.compliance_requirement
            else (doc.document_name or doc.filename or "Document")
        )
        expiry_date_str = doc.expiry_date.isoformat()
        escalation_level = _days_remaining_to_escalation_level(days_remaining)
        item = {
            "user_id": str(doc.user_id),
            "email": doc.user.email if doc.user else "",
            "compliance_name": compliance_name,
            "expiry_date": expiry_date_str,
            "days_remaining": days_remaining,
            "reminder_type": reminder_type,
            "escalation_level": escalation_level,
        }
        reminders.append(item)
        if not item["email"]:
            continue
        existing = (
            db.query(ComplianceReminder)
            .filter(
                ComplianceReminder.document_id == doc.id,
                ComplianceReminder.reminder_type == reminder_type,
            )
            .first()
        )
        if existing:
            continue
        subject = _compliance_reminder_email_subject(compliance_name)
        body = _compliance_reminder_email_body(compliance_name, expiry_date_str, days_remaining)
        success, _ = send_email(item["email"], subject, body)
        if success:
            db.add(ComplianceReminder(document_id=doc.id, reminder_type=reminder_type))
            db.commit()
            logger.info(
                "[COMPLIANCE REMINDER SENT] user_id=%s email=%s compliance_name=%s reminder_type=%s",
                item["user_id"],
                item["email"],
                compliance_name,
                reminder_type,
            )
        else:
            logger.warning("Compliance reminder email failed for %s", item["email"])

        # Multi-level escalation: notify contacts whose level and escalation_trigger_days match
        if doc.unit_id:
            # Expired + daily escalation: send to Level 3 at most once per day per document
            if days_remaining < 0:
                already_sent_today = (
                    db.query(ComplianceEscalationLog)
                    .filter(
                        ComplianceEscalationLog.document_id == doc.id,
                        ComplianceEscalationLog.escalation_level == 3,
                        cast(ComplianceEscalationLog.sent_at, Date) == today,
                    )
                    .first()
                )
                if already_sent_today:
                    pass  # skip escalation for this document today
                else:
                    _send_escalation_for_doc(
                        db, doc, compliance_name, expiry_date_str, days_remaining,
                        escalation_level, today, send_email,
                    )
            else:
                _send_escalation_for_doc(
                    db, doc, compliance_name, expiry_date_str, days_remaining,
                    escalation_level, today, send_email,
                )
    return reminders


def get_documents_requiring_reminder(db: Session) -> list[Document]:
    """
    Return documents that are due for a reminder: they have an expiry date,
    are not yet expired, and are within the reminder window.
    Excludes documents that already had a reminder sent today (idempotent).

    Criteria:
    - expiry_date IS NOT NULL
    - expiry_date >= today (not expired)
    - expiry_date - reminder_days <= today (within reminder window)
    - no reminder_log for this document with sent_at date = today
    """
    today = date.today()
    sent_today_subq = (
        db.query(ReminderLog.document_id)
        .filter(cast(ReminderLog.sent_at, Date) == today)
        .distinct()
    )
    stmt = (
        db.query(Document)
        .filter(
            Document.expiry_date.isnot(None),
            Document.expiry_date >= today,
            text("(documents.expiry_date - documents.reminder_days) <= :today").bindparams(today=today),
            ~Document.id.in_(sent_today_subq),
        )
    )
    return list(stmt.all())
