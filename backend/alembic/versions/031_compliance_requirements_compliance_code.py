"""Add compliance_code to compliance_requirements for standardized manufacturing base.

Revision ID: 031
Revises: 030
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "031"
down_revision: Union[str, None] = "030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "compliance_requirements",
        sa.Column("compliance_code", sa.String(length=64), nullable=True),
    )
    op.create_index(
        op.f("ix_compliance_requirements_compliance_code"),
        "compliance_requirements",
        ["compliance_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_compliance_requirements_compliance_code"),
        table_name="compliance_requirements",
    )
    op.drop_column("compliance_requirements", "compliance_code")
