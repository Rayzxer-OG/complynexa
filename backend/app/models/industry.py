"""Industry master: core manufacturing industries only. Stable industry_id, no reuse."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Industry(Base):
    """
    Master list of industries supported by the MVP (manufacturing only).
    industry_id is stable and used in units.industry, compliance_requirements.industry,
    and industry_compliance_mapping.industry_id.
    """

    __tablename__ = "industries"

    industry_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    industry_name: Mapped[str] = mapped_column(String(256), nullable=False)
