"""Compliance requirement template (master list by industry and applicability rules)."""

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ComplianceRequirement(Base):
    """Master list of compliance types; applicability filtered by industry, employees, load, manufacturing."""

    __tablename__ = "compliance_requirements"

    compliance_code: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    industry: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    compliance_name: Mapped[str] = mapped_column(String(256), nullable=False)
    issuing_authority: Mapped[str | None] = mapped_column(String(256), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    applicability_flag: Mapped[str | None] = mapped_column(String(1), nullable=True)  # M=Mandatory, C=Conditional, O=Optional
    risk_weight: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conditional_question: Mapped[str | None] = mapped_column(Text, nullable=True)  # For C: e.g. "Does your unit generate hazardous waste?"
    renewal_frequency_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    applies_if_manufacturing: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    min_employees: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_connected_load_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
