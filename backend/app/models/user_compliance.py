"""User/unit-specific compliance checklist (required compliances per unit)."""

from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserCompliance(Base):
    """Tracks which compliances are required for a unit and their status."""

    __tablename__ = "user_compliance"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    unit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=False,
    )
    compliance_requirement_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("compliance_requirements.id", ondelete="CASCADE"),
        nullable=False,
    )
    compliance_name: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # pending | uploaded | expired | valid

    unit = relationship("Unit", back_populates="user_compliances")
    compliance_requirement = relationship("ComplianceRequirement", backref="user_compliances")
