"""Add unit attributes for compliance recalculation: hazardous_flag, boiler_flag, built_up_area

Revision ID: 020
Revises: 019
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "020"
down_revision: Union[str, None] = "019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "units",
        sa.Column("hazardous_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "units",
        sa.Column("boiler_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "units",
        sa.Column("built_up_area", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("units", "built_up_area")
    op.drop_column("units", "boiler_flag")
    op.drop_column("units", "hazardous_flag")
