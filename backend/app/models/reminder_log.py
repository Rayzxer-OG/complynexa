"""Reminder log: tracks when reminders were sent per document and type to prevent duplicates."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ReminderLog(Base):
    """
    Record of a reminder sent for a document.
    reminder_type: days_30, days_15, days_7, days_3, days_1, expiry, escalation.
    Unique on (document_id, reminder_type) to prevent duplicate reminders.
    """

    __tablename__ = "reminder_logs"
    __table_args__ = (UniqueConstraint("document_id", "reminder_type", name="uq_reminder_logs_document_id_reminder_type"),)

    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reminder_type: Mapped[str] = mapped_column(String(32), nullable=False)
    sent_to_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 1, 2, or 3 when sent to escalation contact; null for primary user reminder
    escalation_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document = relationship("Document", back_populates="reminder_logs")

    def __repr__(self) -> str:
        return f"<ReminderLog(id={self.id}, document_id={self.document_id}, reminder_type={self.reminder_type}, sent_at={self.sent_at})>"
