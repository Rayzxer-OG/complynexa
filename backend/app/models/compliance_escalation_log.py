"""Log of compliance escalation emails sent (for daily expired escalation dedup)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ComplianceEscalationLog(Base):
    """Record of an escalation email sent for a document (used to avoid duplicate daily escalation)."""

    __tablename__ = "compliance_escalation_log"

    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    escalation_level: Mapped[int] = mapped_column(Integer, nullable=False)
    sent_to_email: Mapped[str] = mapped_column(String(255), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document = relationship("Document", back_populates="compliance_escalation_logs")
