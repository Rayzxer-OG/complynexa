"""Unit attribute: key-value store for conditional compliance (e.g. hazardous_waste_required)."""

from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def attribute_value_to_bool(value: str | None) -> bool:
    """Interpret attribute_value as boolean. 'true', '1', non-zero numeric -> True."""
    if not value:
        return False
    v = value.strip().lower()
    if v in ("true", "1", "yes"):
        return True
    if v in ("false", "0", "no"):
        return False
    try:
        return float(v) != 0
    except ValueError:
        return False


class UnitAttribute(Base):
    """Stores unit-level attributes (boolean or numeric) used by conditional compliance logic."""

    __tablename__ = "unit_attributes"

    unit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attribute_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    attribute_value: Mapped[str] = mapped_column(String(128), nullable=False)

    unit = relationship("Unit", back_populates="unit_attributes")

    __table_args__ = (
        UniqueConstraint("unit_id", "attribute_key", name="uq_unit_attributes_unit_key"),
    )
