"""Create unit_condition_responses table for conditional question answers.

Stores user responses to conditional questions (condition_key -> value) separately
from compliance documents. Value stored as text; can represent boolean, numeric, or string.

Revision ID: 027
Revises: 026
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "027"
down_revision: Union[str, None] = "026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "unit_condition_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("condition_key", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("unit_id", "condition_key", name="uq_unit_condition_responses_unit_key"),
    )
    op.create_index(
        op.f("ix_unit_condition_responses_unit_id"),
        "unit_condition_responses",
        ["unit_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_unit_condition_responses_condition_key"),
        "unit_condition_responses",
        ["condition_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_unit_condition_responses_condition_key"), table_name="unit_condition_responses")
    op.drop_index(op.f("ix_unit_condition_responses_unit_id"), table_name="unit_condition_responses")
    op.drop_table("unit_condition_responses")
