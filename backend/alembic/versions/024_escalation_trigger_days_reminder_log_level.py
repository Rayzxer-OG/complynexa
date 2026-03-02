"""Add escalation_trigger_days to unit_escalation_contacts, escalation_level to reminder_logs, compliance_escalation_log table.

Revision ID: 024
Revises: 023
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "024"
down_revision: Union[str, None] = "023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # unit_escalation_contacts: add escalation_trigger_days (days before expiry: 30, 15, 7, 3, 0)
    op.add_column(
        "unit_escalation_contacts",
        sa.Column("escalation_trigger_days", sa.Integer(), nullable=True),
    )
    # Backfill from escalation_trigger
    op.execute("""
        UPDATE unit_escalation_contacts
        SET escalation_trigger_days = CASE
            WHEN escalation_trigger = '7_days_before_expiry' THEN 7
            WHEN escalation_trigger = '3_days_before_expiry' THEN 3
            WHEN escalation_trigger = 'on_expiry' THEN 0
            ELSE NULL
        END
    """)
    # Leave nullable so legacy rows with unknown escalation_trigger do not break

    # reminder_logs: add escalation_level (1, 2, 3; null for primary user reminders)
    op.add_column(
        "reminder_logs",
        sa.Column("escalation_level", sa.Integer(), nullable=True),
    )

    # compliance_escalation_log: track escalation sends for "already sent today" (daily expired escalation)
    op.create_table(
        "compliance_escalation_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("escalation_level", sa.Integer(), nullable=False),
        sa.Column("sent_to_email", sa.String(length=255), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
    )
    op.create_index(
        op.f("ix_compliance_escalation_log_document_id"),
        "compliance_escalation_log",
        ["document_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_compliance_escalation_log_document_id"), table_name="compliance_escalation_log")
    op.drop_table("compliance_escalation_log")
    op.drop_column("reminder_logs", "escalation_level")
    op.drop_column("unit_escalation_contacts", "escalation_trigger_days")
