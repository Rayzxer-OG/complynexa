"""Seed industry_compliance_mapping for core manufacturing industries from matrix.

Maps each industry to compliances with M/C/O and risk_weight (M 10-20, C 5-10, O 2-5).
Conditional (C) entries include condition_key and condition_question.
Skips if mapping already exists for (industry_id, compliance_requirement_id, state_id NULL).

Revision ID: 033
Revises: 032
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "033"
down_revision: Union[str, None] = "032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Condition key and question for Conditional (C) compliances
CONDITION_FOR_C = {
    "HAZARDOUS_WASTE": (
        "hazardous_waste_generated",
        "Does your unit generate hazardous waste?",
    ),
    "MSIHC": (
        "hazardous_chemicals_used",
        "Does your unit manufacture, store, or import hazardous chemicals?",
    ),
    "PESO_LICENSE": (
        "petroleum_explosives_stored",
        "Does your unit store or handle petroleum or explosives?",
    ),
    "BOILER_LICENSE": (
        "boiler_operated",
        "Does your unit operate a boiler?",
    ),
}

# (compliance_code, applicability_flag, risk_weight). M=10-20, C=5-10, O=2-5
# Table 1: core manufacturing industries and their compliance matrix
INDUSTRY_MATRIX = {
    "Pharmaceutical": [
        ("FACTORY_LICENSE", "M", 15),
        ("POLLUTION_CTE_CTO", "M", 15),
        ("FIRE_NOC", "M", 15),
        ("ELECTRICAL_APPROVAL", "M", 15),
        ("HAZARDOUS_WASTE", "C", 7),
        ("MSIHC", "C", 7),
        ("PESO_LICENSE", "C", 7),
        ("BOILER_LICENSE", "C", 7),
        ("DRUG_LICENSE", "M", 15),
        ("FSSAI_LICENSE", "O", 3),
        ("EXCISE_LICENSE", "O", 3),
    ],
    "Chemical": [
        ("FACTORY_LICENSE", "M", 15),
        ("POLLUTION_CTE_CTO", "M", 15),
        ("FIRE_NOC", "M", 15),
        ("ELECTRICAL_APPROVAL", "M", 15),
        ("HAZARDOUS_WASTE", "M", 15),
        ("MSIHC", "C", 7),
        ("PESO_LICENSE", "C", 7),
        ("BOILER_LICENSE", "C", 7),
        ("DRUG_LICENSE", "O", 3),
        ("FSSAI_LICENSE", "O", 3),
        ("EXCISE_LICENSE", "O", 3),
    ],
    "Engineering / Fabrication": [
        ("FACTORY_LICENSE", "M", 15),
        ("POLLUTION_CTE_CTO", "M", 15),
        ("FIRE_NOC", "M", 15),
        ("ELECTRICAL_APPROVAL", "M", 15),
        ("HAZARDOUS_WASTE", "C", 7),
        ("MSIHC", "C", 7),
        ("PESO_LICENSE", "C", 7),
        ("BOILER_LICENSE", "C", 7),
        ("DRUG_LICENSE", "O", 3),
        ("FSSAI_LICENSE", "O", 3),
        ("EXCISE_LICENSE", "O", 3),
    ],
    "Distillery / Brewery": [
        ("FACTORY_LICENSE", "M", 15),
        ("POLLUTION_CTE_CTO", "M", 15),
        ("FIRE_NOC", "M", 15),
        ("ELECTRICAL_APPROVAL", "M", 15),
        ("HAZARDOUS_WASTE", "C", 7),
        ("MSIHC", "C", 7),
        ("PESO_LICENSE", "C", 7),
        ("BOILER_LICENSE", "C", 7),
        ("DRUG_LICENSE", "O", 3),
        ("FSSAI_LICENSE", "O", 3),
        ("EXCISE_LICENSE", "M", 15),
    ],
    "Food Processing": [
        ("FACTORY_LICENSE", "M", 15),
        ("POLLUTION_CTE_CTO", "M", 15),
        ("FIRE_NOC", "M", 15),
        ("ELECTRICAL_APPROVAL", "M", 15),
        ("HAZARDOUS_WASTE", "C", 7),
        ("MSIHC", "C", 7),
        ("PESO_LICENSE", "C", 7),
        ("BOILER_LICENSE", "C", 7),
        ("DRUG_LICENSE", "O", 3),
        ("FSSAI_LICENSE", "M", 15),
        ("EXCISE_LICENSE", "O", 3),
    ],
    "Plastic / Polymer": [
        ("FACTORY_LICENSE", "M", 15),
        ("POLLUTION_CTE_CTO", "M", 15),
        ("FIRE_NOC", "M", 15),
        ("ELECTRICAL_APPROVAL", "M", 15),
        ("HAZARDOUS_WASTE", "C", 7),
        ("MSIHC", "C", 7),
        ("PESO_LICENSE", "C", 7),
        ("BOILER_LICENSE", "C", 7),
        ("DRUG_LICENSE", "O", 3),
        ("FSSAI_LICENSE", "O", 3),
        ("EXCISE_LICENSE", "O", 3),
    ],
    "Textile (non-dyeing)": [
        ("FACTORY_LICENSE", "M", 15),
        ("POLLUTION_CTE_CTO", "M", 15),
        ("FIRE_NOC", "M", 15),
        ("ELECTRICAL_APPROVAL", "M", 15),
        ("HAZARDOUS_WASTE", "C", 7),
        ("MSIHC", "C", 7),
        ("PESO_LICENSE", "C", 7),
        ("BOILER_LICENSE", "C", 7),
        ("DRUG_LICENSE", "O", 3),
        ("FSSAI_LICENSE", "O", 3),
        ("EXCISE_LICENSE", "O", 3),
    ],
    "Textile (dyeing)": [
        ("FACTORY_LICENSE", "M", 15),
        ("POLLUTION_CTE_CTO", "M", 15),
        ("FIRE_NOC", "M", 15),
        ("ELECTRICAL_APPROVAL", "M", 15),
        ("HAZARDOUS_WASTE", "M", 15),
        ("MSIHC", "C", 7),
        ("PESO_LICENSE", "C", 7),
        ("BOILER_LICENSE", "C", 7),
        ("DRUG_LICENSE", "O", 3),
        ("FSSAI_LICENSE", "O", 3),
        ("EXCISE_LICENSE", "O", 3),
    ],
    "Paper & Pulp": [
        ("FACTORY_LICENSE", "M", 15),
        ("POLLUTION_CTE_CTO", "M", 15),
        ("FIRE_NOC", "M", 15),
        ("ELECTRICAL_APPROVAL", "M", 15),
        ("HAZARDOUS_WASTE", "C", 7),
        ("MSIHC", "C", 7),
        ("PESO_LICENSE", "C", 7),
        ("BOILER_LICENSE", "C", 7),
        ("DRUG_LICENSE", "O", 3),
        ("FSSAI_LICENSE", "O", 3),
        ("EXCISE_LICENSE", "O", 3),
    ],
    "Automobile / Auto Parts": [
        ("FACTORY_LICENSE", "M", 15),
        ("POLLUTION_CTE_CTO", "M", 15),
        ("FIRE_NOC", "M", 15),
        ("ELECTRICAL_APPROVAL", "M", 15),
        ("HAZARDOUS_WASTE", "C", 7),
        ("MSIHC", "C", 7),
        ("PESO_LICENSE", "C", 7),
        ("BOILER_LICENSE", "C", 7),
        ("DRUG_LICENSE", "O", 3),
        ("FSSAI_LICENSE", "O", 3),
        ("EXCISE_LICENSE", "O", 3),
    ],
    "Electronics Manufacturing": [
        ("FACTORY_LICENSE", "M", 15),
        ("POLLUTION_CTE_CTO", "M", 15),
        ("FIRE_NOC", "M", 15),
        ("ELECTRICAL_APPROVAL", "M", 15),
        ("HAZARDOUS_WASTE", "C", 7),
        ("MSIHC", "C", 7),
        ("PESO_LICENSE", "C", 7),
        ("BOILER_LICENSE", "C", 7),
        ("DRUG_LICENSE", "O", 3),
        ("FSSAI_LICENSE", "O", 3),
        ("EXCISE_LICENSE", "O", 3),
    ],
}


# Backfill compliance_code on existing rows (e.g. from old seed) so mapping can resolve req id
BACKFILL_NAME_TO_CODE = [
    ("Factory License", "FACTORY_LICENSE"),
    ("Consent to Establish / Consent to Operate", "POLLUTION_CTE_CTO"),
    ("MP Pollution Control Board Consent to Establish", "POLLUTION_CTE_CTO"),
    ("MP Pollution Control Board Consent to Operate", "POLLUTION_CTE_CTO"),
    ("MPCB Consent", "POLLUTION_CTE_CTO"),
    ("Fire NOC", "FIRE_NOC"),
    ("Electrical Approval", "ELECTRICAL_APPROVAL"),
    ("Electrical Safety Certificate", "ELECTRICAL_APPROVAL"),
    ("Electrical Safety", "ELECTRICAL_APPROVAL"),
    ("Hazardous Waste Authorization", "HAZARDOUS_WASTE"),
    ("Hazardous Chemical Storage License", "MSIHC"),
    ("MSIHC (Manufacturing, Storage, Import of Hazardous Chemicals)", "MSIHC"),
    ("PESO License", "PESO_LICENSE"),
    ("Boiler License", "BOILER_LICENSE"),
    ("Drug Manufacturing License", "DRUG_LICENSE"),
    ("FSSAI License", "FSSAI_LICENSE"),
    ("Excise License", "EXCISE_LICENSE"),
]


def upgrade() -> None:
    conn = op.get_bind()
    # Backfill compliance_code so (industry, compliance_code) resolves for all industries
    for name, code in BACKFILL_NAME_TO_CODE:
        conn.execute(
            sa.text(
                """
                UPDATE compliance_requirements
                SET compliance_code = :code
                WHERE compliance_code IS NULL AND TRIM(compliance_name) = :name
                """
            ),
            {"code": code, "name": name.strip()},
        )
    for industry_id, items in INDUSTRY_MATRIX.items():
        for compliance_code, flag, risk in items:
            # Resolve compliance_requirement_id from compliance_requirements (industry + compliance_code)
            row = conn.execute(
                sa.text(
                    """
                    SELECT id FROM compliance_requirements
                    WHERE industry = :industry AND compliance_code = :code
                    LIMIT 1
                    """
                ),
                {"industry": industry_id, "code": compliance_code},
            ).first()
            if not row:
                continue
            req_id = row[0]
            # Skip if mapping already exists (industry-level, state_id NULL)
            exists = conn.execute(
                sa.text(
                    """
                    SELECT 1 FROM industry_compliance_mapping
                    WHERE industry_id = :industry_id AND compliance_requirement_id = :req_id AND state_id IS NULL
                    LIMIT 1
                    """
                ),
                {"industry_id": industry_id, "req_id": req_id},
            ).scalar()
            if exists:
                continue
            # For C we need condition_key and condition_question (DB CHECK)
            cond_key = None
            cond_question = None
            if flag == "C" and compliance_code in CONDITION_FOR_C:
                cond_key, cond_question = CONDITION_FOR_C[compliance_code]
            conn.execute(
                sa.text(
                    """
                    INSERT INTO industry_compliance_mapping
                    (id, industry_id, state_id, compliance_requirement_id, applicability_flag,
                     condition_key, condition_question, condition_type, risk_weight,
                     state_override_possible, override_flag)
                    VALUES (gen_random_uuid(), :industry_id, NULL, :req_id, :flag, :cond_key, :cond_question,
                            :cond_type, :risk, false, false)
                    """
                ),
                {
                    "industry_id": industry_id,
                    "req_id": req_id,
                    "flag": flag,
                    "cond_key": cond_key,
                    "cond_question": cond_question,
                    "cond_type": "boolean" if flag == "C" else None,
                    "risk": risk,
                },
            )


def downgrade() -> None:
    conn = op.get_bind()
    for industry_id, items in INDUSTRY_MATRIX.items():
        for compliance_code, _flag, _risk in items:
            row = conn.execute(
                sa.text(
                    """
                    SELECT id FROM compliance_requirements
                    WHERE industry = :industry AND compliance_code = :code
                    LIMIT 1
                    """
                ),
                {"industry": industry_id, "code": compliance_code},
            ).first()
            if not row:
                continue
            req_id = row[0]
            conn.execute(
                sa.text(
                    """
                    DELETE FROM industry_compliance_mapping
                    WHERE industry_id = :industry_id AND compliance_requirement_id = :req_id AND state_id IS NULL
                    """
                ),
                {"industry_id": industry_id, "req_id": req_id},
            )
