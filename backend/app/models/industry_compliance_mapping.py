"""Industry–compliance mapping: applicability and risk per industry."""

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class IndustryComplianceMapping(Base):
    """
    Maps (industry_id, state_id?, compliance_requirement_id) to applicability and risk.

    Columns: applicability_flag (M/C/O), condition_key, condition_question, condition_type,
    risk_weight, state_id. Unique: (industry_id, compliance_requirement_id, state_id) via partial indexes.

    Rules (enforced by DB CHECK):
    - If applicability_flag = 'C': condition_key and condition_question must not be null.
    - If applicability_flag != 'C': condition_key must be null.

    condition_type: 'boolean' | 'numeric' | 'select' for backend-driven dynamic conditions (C only).
    """

    __tablename__ = "industry_compliance_mapping"

    industry_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    state_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    compliance_requirement_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("compliance_requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    applicability_flag: Mapped[str] = mapped_column(String(1), nullable=False)  # M, C, O
    condition_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    condition_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    condition_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # boolean, numeric, select
    risk_weight: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state_override_possible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    override_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    compliance_requirement = relationship(
        "ComplianceRequirement",
        backref="industry_compliance_mappings",
    )

    __table_args__ = ()
