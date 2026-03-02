"""Create industries master table with core manufacturing industries only.

Stable industry_id values; no generic placeholders (Manufacturing, Other, Retail, Healthcare).
MVP focuses on manufacturing industries only.

Revision ID: 030
Revises: 029
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "030"
down_revision: Union[str, None] = "029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Core manufacturing industries only. industry_id is stable (not reused); same as name for compatibility.
CORE_MANUFACTURING_INDUSTRIES = [
    "Engineering / Fabrication",
    "Pharmaceutical",
    "Chemical",
    "Distillery / Brewery",
    "Food Processing",
    "Plastic / Polymer",
    "Textile (non-dyeing)",
    "Textile (dyeing)",
    "Paper & Pulp",
    "Automobile / Auto Parts",
    "Electronics Manufacturing",
]


def upgrade() -> None:
    op.create_table(
        "industries",
        sa.Column("industry_id", sa.String(length=128), nullable=False),
        sa.Column("industry_name", sa.String(length=256), nullable=False),
        sa.PrimaryKeyConstraint("industry_id"),
    )

    conn = op.get_bind()
    for name in CORE_MANUFACTURING_INDUSTRIES:
        conn.execute(
            sa.text(
                "INSERT INTO industries (industry_id, industry_name) VALUES (:id, :name)"
            ),
            {"id": name, "name": name},
        )


def downgrade() -> None:
    op.drop_table("industries")
