"""Add unit_compliance_attributes and conditional_question to compliance_requirements

Revision ID: 017
Revises: 016
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "compliance_requirements",
        sa.Column("conditional_question", sa.Text(), nullable=True),
    )
    op.create_table(
        "unit_compliance_attributes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("compliance_requirement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("applies", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["compliance_requirement_id"], ["compliance_requirements.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("unit_id", "compliance_requirement_id", name="uq_unit_compliance_attributes_unit_req"),
    )
    op.create_index(
        op.f("ix_unit_compliance_attributes_unit_id"),
        "unit_compliance_attributes",
        ["unit_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_unit_compliance_attributes_unit_id"), table_name="unit_compliance_attributes")
    op.drop_table("unit_compliance_attributes")
    op.drop_column("compliance_requirements", "conditional_question")
