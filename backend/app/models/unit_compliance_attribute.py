"""Unit-specific answer to a conditional compliance question."""

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UnitComplianceAttribute(Base):
    """Stores whether a conditional compliance applies to a unit (user's Yes/No answer)."""

    __tablename__ = "unit_compliance_attributes"

    unit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    compliance_requirement_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("compliance_requirements.id", ondelete="CASCADE"),
        nullable=False,
    )
    applies: Mapped[bool] = mapped_column(Boolean, nullable=False)

    unit = relationship("Unit", back_populates="unit_compliance_attributes")
    compliance_requirement = relationship("ComplianceRequirement", backref="unit_compliance_attributes")

    __table_args__ = (
        UniqueConstraint("unit_id", "compliance_requirement_id", name="uq_unit_compliance_attributes_unit_req"),
    )
