"""Add compliance_profile_completed to units.

When false, dashboard/checklist/risk endpoints return PROFILE_SETUP_REQUIRED.
Set to true after successful POST /units/{id}/compliance-attributes.

Revision ID: 028
Revises: 027
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "028"
down_revision: Union[str, None] = "027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "units",
        sa.Column("compliance_profile_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("units", "compliance_profile_completed")
