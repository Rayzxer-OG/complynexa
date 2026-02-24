"""
Cron script: find documents requiring reminder and send reminders.

Idempotent: running multiple times per day does not resend for the same document.
Run from backend directory:
  python -m app.scripts.run_reminders

Or:
  python app/scripts/run_reminders.py
"""
from app.core.database import SessionLocal
from app.services.email_service import send_email_reminder
from app.services.reminder_service import get_documents_requiring_reminder


def main() -> None:
    db = SessionLocal()
    try:
        documents = get_documents_requiring_reminder(db)
        for document in documents:
            try:
                send_email_reminder(document, db)
                db.commit()
            except Exception:
                db.rollback()
                raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
