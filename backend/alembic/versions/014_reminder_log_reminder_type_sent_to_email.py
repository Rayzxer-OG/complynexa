"""Add reminder_type, sent_to_email and unique (document_id, reminder_type) to reminder_logs

Revision ID: 014
Revises: 013
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reminder_logs",
        sa.Column("reminder_type", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "reminder_logs",
        sa.Column("sent_to_email", sa.String(length=255), nullable=True),
    )
    op.execute("UPDATE reminder_logs SET reminder_type = 'legacy' WHERE reminder_type IS NULL")
    op.alter_column(
        "reminder_logs",
        "reminder_type",
        existing_type=sa.String(length=32),
        nullable=False,
    )
    # Deduplicate: keep one row per (document_id, reminder_type) for legacy
    op.execute("""
        DELETE FROM reminder_logs a
        USING reminder_logs b
        WHERE a.id > b.id AND a.document_id = b.document_id AND a.reminder_type = b.reminder_type
    """)
    op.create_unique_constraint(
        "uq_reminder_logs_document_id_reminder_type",
        "reminder_logs",
        ["document_id", "reminder_type"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_reminder_logs_document_id_reminder_type",
        "reminder_logs",
        type_="unique",
    )
    op.drop_column("reminder_logs", "sent_to_email")
    op.drop_column("reminder_logs", "reminder_type")
