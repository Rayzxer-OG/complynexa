"""Compliance requirements, units, user_compliance tables

Revision ID: 011
Revises: 010
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "compliance_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("industry", sa.String(length=128), nullable=False),
        sa.Column("compliance_name", sa.String(length=256), nullable=False),
        sa.Column("issuing_authority", sa.String(length=256), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("mandatory", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("renewal_frequency_months", sa.Integer(), nullable=True),
        sa.Column("applies_if_manufacturing", sa.Boolean(), nullable=True),
        sa.Column("min_employees", sa.Integer(), nullable=True),
        sa.Column("min_connected_load_kw", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_compliance_requirements_industry"), "compliance_requirements", ["industry"], unique=False)

    op.create_table(
        "units",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_name", sa.String(length=256), nullable=False),
        sa.Column("unit_name", sa.String(length=256), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("state", sa.String(length=128), nullable=False),
        sa.Column("industry", sa.String(length=128), nullable=False),
        sa.Column("business_type", sa.String(length=128), nullable=False),
        sa.Column("number_of_employees", sa.Integer(), nullable=False),
        sa.Column("manufacturing", sa.Boolean(), nullable=False),
        sa.Column("connected_load_kw", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_units_user_id"), "units", ["user_id"], unique=False)

    op.create_table(
        "user_compliance",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("compliance_requirement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("compliance_name", sa.String(length=256), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["compliance_requirement_id"], ["compliance_requirements.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_user_compliance_unit_id"), "user_compliance", ["unit_id"], unique=False)
    op.create_index(op.f("ix_user_compliance_user_id"), "user_compliance", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_compliance_user_id"), table_name="user_compliance")
    op.drop_index(op.f("ix_user_compliance_unit_id"), table_name="user_compliance")
    op.drop_table("user_compliance")
    op.drop_index(op.f("ix_units_user_id"), table_name="units")
    op.drop_table("units")
    op.drop_index(op.f("ix_compliance_requirements_industry"), table_name="compliance_requirements")
    op.drop_table("compliance_requirements")
