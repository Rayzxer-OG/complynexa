"""Add sequence_number and source_document_name to certificates

Revision ID: 009
Revises: 008
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "certificates",
        sa.Column("sequence_number", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "certificates",
        sa.Column("source_document_name", sa.String(length=512), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("certificates", "source_document_name")
    op.drop_column("certificates", "sequence_number")
