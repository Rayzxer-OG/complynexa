"""Add industry_compliance_mapping table

Revision ID: 018
Revises: 017
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "industry_compliance_mapping",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("industry_id", sa.String(length=128), nullable=False),
        sa.Column("compliance_requirement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("applicability_flag", sa.String(length=1), nullable=False),
        sa.Column("risk_weight", sa.Integer(), nullable=True),
        sa.Column("state_override_possible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["compliance_requirement_id"],
            ["compliance_requirements.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "industry_id",
            "compliance_requirement_id",
            name="uq_industry_compliance_mapping_industry_req",
        ),
    )
    op.create_index(
        op.f("ix_industry_compliance_mapping_industry_id"),
        "industry_compliance_mapping",
        ["industry_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_industry_compliance_mapping_compliance_requirement_id"),
        "industry_compliance_mapping",
        ["compliance_requirement_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_industry_compliance_mapping_compliance_requirement_id"),
        table_name="industry_compliance_mapping",
    )
    op.drop_index(
        op.f("ix_industry_compliance_mapping_industry_id"),
        table_name="industry_compliance_mapping",
    )
    op.drop_table("industry_compliance_mapping")
