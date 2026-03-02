"""Add spcb_category to units for compliance recalculation

Revision ID: 023
Revises: 022
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "023"
down_revision: Union[str, None] = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "units",
        sa.Column("spcb_category", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("units", "spcb_category")
