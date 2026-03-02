"""Add state_id and override_flag to industry_compliance_mapping for state-level override

Revision ID: 021
Revises: 020
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "021"
down_revision: Union[str, None] = "020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "industry_compliance_mapping",
        sa.Column("state_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "industry_compliance_mapping",
        sa.Column("override_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        op.f("ix_industry_compliance_mapping_state_id"),
        "industry_compliance_mapping",
        ["state_id"],
        unique=False,
    )
    op.drop_constraint(
        "uq_industry_compliance_mapping_industry_req",
        "industry_compliance_mapping",
        type_="unique",
    )
    op.create_index(
        "ix_industry_compliance_mapping_industry_state_req",
        "industry_compliance_mapping",
        ["industry_id", "state_id", "compliance_requirement_id"],
        unique=True,
        postgresql_where=sa.text("state_id IS NOT NULL"),
    )
    op.create_index(
        "ix_industry_compliance_mapping_industry_req_default",
        "industry_compliance_mapping",
        ["industry_id", "compliance_requirement_id"],
        unique=True,
        postgresql_where=sa.text("state_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_industry_compliance_mapping_industry_req_default",
        table_name="industry_compliance_mapping",
    )
    op.drop_index(
        "ix_industry_compliance_mapping_industry_state_req",
        table_name="industry_compliance_mapping",
    )
    op.create_unique_constraint(
        "uq_industry_compliance_mapping_industry_req",
        "industry_compliance_mapping",
        ["industry_id", "compliance_requirement_id"],
    )
    op.drop_index(
        op.f("ix_industry_compliance_mapping_state_id"),
        table_name="industry_compliance_mapping",
    )
    op.drop_column("industry_compliance_mapping", "override_flag")
    op.drop_column("industry_compliance_mapping", "state_id")
