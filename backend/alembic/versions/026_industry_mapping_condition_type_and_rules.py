"""Add condition_type and enforce conditional logic rules on industry_compliance_mapping.

Rules:
- If applicability_flag = 'C': condition_key and condition_question must not be null.
- If applicability_flag != 'C': condition_key must be null.

Unique: industry_id + compliance_requirement_id + state_id is already enforced by
partial unique indexes (021): one per (industry_id, state_id, compliance_requirement_id)
when state_id IS NOT NULL, and one per (industry_id, compliance_requirement_id) when state_id IS NULL.

Revision ID: 026
Revises: 025
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "026"
down_revision: Union[str, None] = "025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add condition_type: 'boolean', 'numeric', 'select' (for C mappings)
    op.add_column(
        "industry_compliance_mapping",
        sa.Column("condition_type", sa.String(length=32), nullable=True),
    )

    # Backfill condition_question for C rows that have null (so CHECK can be applied)
    op.execute("""
        UPDATE industry_compliance_mapping
        SET condition_question = 'Does your unit have ' || REPLACE(condition_key, '_', ' ') || '?'
        WHERE UPPER(TRIM(applicability_flag)) = 'C'
          AND condition_key IS NOT NULL
          AND (condition_question IS NULL OR TRIM(condition_question) = '')
    """)
    # C rows with null condition_key cannot satisfy the new CHECK; treat as optional
    op.execute("""
        UPDATE industry_compliance_mapping
        SET applicability_flag = 'O'
        WHERE UPPER(TRIM(applicability_flag)) = 'C'
          AND condition_key IS NULL
    """)

    # Rules: C => condition_key and condition_question NOT NULL; non-C => condition_key NULL
    op.create_check_constraint(
        "ck_industry_compliance_mapping_conditional_rules",
        "industry_compliance_mapping",
        sa.text(
            "((UPPER(TRIM(applicability_flag)) = 'C' AND condition_key IS NOT NULL AND condition_question IS NOT NULL AND TRIM(condition_question) != '') "
            "OR ((UPPER(TRIM(applicability_flag)) <> 'C' OR applicability_flag IS NULL) AND condition_key IS NULL))"
        ),
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_industry_compliance_mapping_conditional_rules",
        "industry_compliance_mapping",
        type_="check",
    )
    op.drop_column("industry_compliance_mapping", "condition_type")
