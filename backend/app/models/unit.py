"""Unit (factory / establishment) belonging to a user."""

from uuid import UUID

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Unit(Base):
    """Factory or business unit with industry and applicability parameters."""

    __tablename__ = "units"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_name: Mapped[str] = mapped_column(String(256), nullable=False)
    unit_name: Mapped[str] = mapped_column(String(256), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(128), nullable=False)
    industry: Mapped[str] = mapped_column(String(128), nullable=False)
    business_type: Mapped[str] = mapped_column(String(128), nullable=False)
    number_of_employees: Mapped[int] = mapped_column(Integer, nullable=False)
    manufacturing: Mapped[bool] = mapped_column(Boolean, nullable=False)
    connected_load_kw: Mapped[float] = mapped_column(Float, nullable=False)
    hazardous_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    boiler_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    built_up_area: Mapped[float | None] = mapped_column(Float, nullable=True)
    spcb_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    compliance_profile_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    compliance_matrix_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    monitoring_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user_compliances = relationship("UserCompliance", back_populates="unit", cascade="all, delete-orphan")
    unit_compliance_attributes = relationship(
        "UnitComplianceAttribute", back_populates="unit", cascade="all, delete-orphan"
    )
    unit_escalation_contacts = relationship(
        "UnitEscalationContact", back_populates="unit", cascade="all, delete-orphan"
    )
    unit_attributes = relationship(
        "UnitAttribute", back_populates="unit", cascade="all, delete-orphan"
    )
    unit_condition_responses = relationship(
        "UnitConditionResponse", back_populates="unit", cascade="all, delete-orphan"
    )
