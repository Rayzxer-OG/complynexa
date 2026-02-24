"""Add document s3_url and create certificates table

Revision ID: 008
Revises: 007
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("s3_url", sa.String(length=1024), nullable=True),
    )
    op.create_table(
        "certificates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_number", sa.String(length=256), nullable=True),
        sa.Column("certificate_name", sa.String(length=512), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("split_pdf_s3_key", sa.String(length=1024), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_certificates_document_id", "certificates", ["document_id"], unique=False)
    op.create_index("ix_certificates_user_id", "certificates", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_certificates_user_id", table_name="certificates")
    op.drop_index("ix_certificates_document_id", table_name="certificates")
    op.drop_table("certificates")
    op.drop_column("documents", "s3_url")
