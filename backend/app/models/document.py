"""Document model."""

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Document(Base):
    """Document with optional Textract-extracted text and LLM-extracted compliance fields."""

    __tablename__ = "documents"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    s3_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reminder_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    compliance_requirement_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("compliance_requirements.id", ondelete="SET NULL"),
        nullable=True,
    )
    unit_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("units.id", ondelete="SET NULL"),
        nullable=True,
    )
    license_number: Mapped[str | None] = mapped_column(String(256), nullable=True)
    issuing_authority: Mapped[str | None] = mapped_column(String(512), nullable=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    document_file_reference: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    user = relationship("User", back_populates="documents")
    reminder_logs = relationship("ReminderLog", back_populates="document", cascade="all, delete-orphan")
    compliance_reminders = relationship("ComplianceReminder", back_populates="document", cascade="all, delete-orphan")
    compliance_escalation_logs = relationship(
        "ComplianceEscalationLog", back_populates="document", cascade="all, delete-orphan"
    )
    certificates = relationship("Certificate", back_populates="document", cascade="all, delete-orphan")
    compliance_requirement = relationship("ComplianceRequirement", backref="documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename})>"
