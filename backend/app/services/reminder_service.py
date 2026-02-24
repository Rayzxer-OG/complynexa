"""Compliance reminder: find documents expiring soon."""

from datetime import date

from sqlalchemy import cast, text
from sqlalchemy.orm import Session
from sqlalchemy.types import Date

from app.models.document import Document
from app.models.reminder_log import ReminderLog


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
