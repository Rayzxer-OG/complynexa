"""Add license_number, issuing_authority, issue_date, document_file_reference to documents

Revision ID: 015
Revises: 014
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("license_number", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("issuing_authority", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("issue_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("document_file_reference", sa.String(length=1024), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("documents", "document_file_reference")
    op.drop_column("documents", "issue_date")
    op.drop_column("documents", "issuing_authority")
    op.drop_column("documents", "license_number")
