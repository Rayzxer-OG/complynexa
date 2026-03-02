"""Scheduler for compliance expiry reminders (daily at 9 AM)."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import SessionLocal
from app.services.reminder_service import check_and_send_compliance_reminders

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None
_started = False


def _run_compliance_reminders() -> None:
    """Job: run compliance reminder check with its own DB session. Does not send email; only prepares data."""
    db = SessionLocal()
    try:
        reminders = check_and_send_compliance_reminders(db)
        if reminders:
            logger.info("Compliance reminders prepared: %s items (no email sent)", len(reminders))
    except Exception:
        logger.exception("Compliance reminder check failed")
    finally:
        db.close()


def start() -> None:
    """Create scheduler, add daily 9 AM job for compliance reminders, and start. Idempotent: runs only once."""
    global _scheduler, _started
    if _started and _scheduler is not None:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _run_compliance_reminders,
        CronTrigger(hour=9, minute=0),
        id="compliance_reminders",
    )
    _scheduler.start()
    _started = True
    logger.info("Compliance reminder scheduler started (daily at 09:00)")


def shutdown() -> None:
    """Stop the scheduler if running."""
    global _scheduler, _started
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        _started = False
        logger.info("Compliance reminder scheduler stopped")
