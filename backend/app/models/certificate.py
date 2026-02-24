"""Certificate model (extracted from a document)."""

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Certificate(Base):
    """Single certificate extracted from a multi-certificate PDF (split by REPORT No.)."""

    __tablename__ = "certificates"

    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_number: Mapped[str | None] = mapped_column(String(256), nullable=True)
    certificate_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    source_document_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    split_pdf_s3_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    document = relationship("Document", back_populates="certificates")
    user = relationship("User", back_populates="certificates")

    def __repr__(self) -> str:
        return f"<Certificate(id={self.id}, report_number={self.report_number})>"
