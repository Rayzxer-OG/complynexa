"""Reminder log: tracks when reminders were sent to avoid duplicates."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ReminderLog(Base):
    """Record of a reminder sent for a document (one per send)."""

    __tablename__ = "reminder_logs"

    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document = relationship("Document", back_populates="reminder_logs")

    def __repr__(self) -> str:
        return f"<ReminderLog(id={self.id}, document_id={self.document_id}, sent_at={self.sent_at})>"
