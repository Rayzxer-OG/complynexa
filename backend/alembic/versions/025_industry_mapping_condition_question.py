"""Add condition_question to industry_compliance_mapping for dynamic questionnaire.

Revision ID: 025
Revises: 024
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "025"
down_revision: Union[str, None] = "024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "industry_compliance_mapping",
        sa.Column("condition_question", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("industry_compliance_mapping", "condition_question")
