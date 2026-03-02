"""Add applicability_flag and risk_weight to compliance_requirements

Revision ID: 016
Revises: 015
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "compliance_requirements",
        sa.Column("applicability_flag", sa.String(length=1), nullable=True),
    )
    op.add_column(
        "compliance_requirements",
        sa.Column("risk_weight", sa.Integer(), nullable=True),
    )
    op.execute(
        "UPDATE compliance_requirements SET applicability_flag = CASE WHEN mandatory THEN 'M' ELSE 'O' END WHERE applicability_flag IS NULL"
    )


def downgrade() -> None:
    op.drop_column("compliance_requirements", "risk_weight")
    op.drop_column("compliance_requirements", "applicability_flag")
