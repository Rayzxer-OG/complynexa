"""Add compliance_matrix_generated and monitoring_active to units.

compliance_matrix_generated: set true after compliance generation engine completes.
monitoring_active: set true after first compliance checklist load.

Revision ID: 029
Revises: 028
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "029"
down_revision: Union[str, None] = "028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "units",
        sa.Column("compliance_matrix_generated", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "units",
        sa.Column("monitoring_active", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("units", "monitoring_active")
    op.drop_column("units", "compliance_matrix_generated")
