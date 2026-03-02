"""Add compliance_requirement_id and unit_id to documents

Revision ID: 012
Revises: 011
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("compliance_requirement_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_documents_compliance_requirement_id",
        "documents",
        "compliance_requirements",
        ["compliance_requirement_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_documents_unit_id",
        "documents",
        "units",
        ["unit_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_documents_unit_id", "documents", type_="foreignkey")
    op.drop_constraint("fk_documents_compliance_requirement_id", "documents", type_="foreignkey")
    op.drop_column("documents", "unit_id")
    op.drop_column("documents", "compliance_requirement_id")
