"""Add user_id to documents

Revision ID: 006
Revises: 005
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    # Assign existing documents to the first user (by created_at)
    op.execute(
        sa.text(
            "UPDATE documents SET user_id = (SELECT id FROM users ORDER BY created_at ASC LIMIT 1)"
        )
    )
    op.alter_column(
        "documents",
        "user_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_documents_user_id_users",
        "documents",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_documents_user_id_users", "documents", type_="foreignkey")
    op.drop_column("documents", "user_id")
