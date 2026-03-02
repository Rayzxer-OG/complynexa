"""Unit condition response: user answer to a conditional compliance question (condition_key -> value)."""

from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UnitConditionResponse(Base):
    """
    Stores user responses to conditional questions, separate from compliance documents.
    One row per (unit_id, condition_key). value is stored as text (boolean: 'true'/'false',
    numeric: string number, string: free text).
    """

    __tablename__ = "unit_condition_responses"

    unit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    condition_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    # created_at, updated_at from Base

    unit = relationship("Unit", back_populates="unit_condition_responses")
