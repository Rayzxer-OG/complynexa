"""Unit escalation contact for compliance reminder escalation."""

from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


# Allowed escalation_trigger values for dropdown (legacy)
ESCALATION_TRIGGER_30_DAYS = "30_days_before_expiry"
ESCALATION_TRIGGER_15_DAYS = "15_days_before_expiry"
ESCALATION_TRIGGER_7_DAYS = "7_days_before_expiry"
ESCALATION_TRIGGER_3_DAYS = "3_days_before_expiry"
ESCALATION_TRIGGER_ON_EXPIRY = "on_expiry"

ESCALATION_TRIGGER_CHOICES = [
    ESCALATION_TRIGGER_30_DAYS,
    ESCALATION_TRIGGER_15_DAYS,
    ESCALATION_TRIGGER_7_DAYS,
    ESCALATION_TRIGGER_3_DAYS,
    ESCALATION_TRIGGER_ON_EXPIRY,
]

# Multi-level escalation: days before expiry when contact is notified (30, 15, 7, 3, 0 = on expiry)
ESCALATION_TRIGGER_DAYS_CHOICES = (30, 15, 7, 3, 0)


def escalation_trigger_to_days_remaining(trigger: str) -> int | None:
    """Map escalation_trigger to days_remaining for reminder matching. Returns None if invalid."""
    if trigger == ESCALATION_TRIGGER_30_DAYS:
        return 30
    if trigger == ESCALATION_TRIGGER_15_DAYS:
        return 15
    if trigger == ESCALATION_TRIGGER_7_DAYS:
        return 7
    if trigger == ESCALATION_TRIGGER_3_DAYS:
        return 3
    if trigger == ESCALATION_TRIGGER_ON_EXPIRY:
        return 0
    return None


def escalation_trigger_days_to_trigger(days: int) -> str:
    """Map escalation_trigger_days to legacy escalation_trigger string."""
    if days == 30:
        return ESCALATION_TRIGGER_30_DAYS
    if days == 15:
        return ESCALATION_TRIGGER_15_DAYS
    if days == 7:
        return ESCALATION_TRIGGER_7_DAYS
    if days == 3:
        return ESCALATION_TRIGGER_3_DAYS
    if days == 0:
        return ESCALATION_TRIGGER_ON_EXPIRY
    return ESCALATION_TRIGGER_7_DAYS  # fallback


class UnitEscalationContact(Base):
    """Escalation contact for a unit: Level 1 (required), 2 and 3 optional."""

    __tablename__ = "unit_escalation_contacts"

    unit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, or 3
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    mobile: Mapped[str | None] = mapped_column(String(32), nullable=True)
    escalation_trigger: Mapped[str] = mapped_column(String(64), nullable=False)
    # Days before expiry when this contact is notified (30, 15, 7, 3, or 0 = on expiry). Used for multi-level escalation.
    escalation_trigger_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    unit = relationship("Unit", back_populates="unit_escalation_contacts")
