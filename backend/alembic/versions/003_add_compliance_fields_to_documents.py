"""Add compliance fields to documents

Revision ID: 003
Revises: 002
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("document_name", sa.String(length=512), nullable=True))
    op.add_column("documents", sa.Column("expiry_date", sa.Date(), nullable=True))
    op.add_column("documents", sa.Column("category", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "category")
    op.drop_column("documents", "expiry_date")
    op.drop_column("documents", "document_name")
