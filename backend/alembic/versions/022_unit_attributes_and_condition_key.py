"""Add unit_attributes table (key-value) and condition_key on industry_compliance_mapping

Revision ID: 022
Revises: 021
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "022"
down_revision: Union[str, None] = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "industry_compliance_mapping",
        sa.Column("condition_key", sa.String(length=128), nullable=True),
    )
    op.create_table(
        "unit_attributes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attribute_key", sa.String(length=128), nullable=False),
        sa.Column("attribute_value", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("unit_id", "attribute_key", name="uq_unit_attributes_unit_key"),
    )
    op.create_index(
        op.f("ix_unit_attributes_unit_id"),
        "unit_attributes",
        ["unit_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_unit_attributes_attribute_key"),
        "unit_attributes",
        ["attribute_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_unit_attributes_attribute_key"), table_name="unit_attributes")
    op.drop_index(op.f("ix_unit_attributes_unit_id"), table_name="unit_attributes")
    op.drop_table("unit_attributes")
    op.drop_column("industry_compliance_mapping", "condition_key")
