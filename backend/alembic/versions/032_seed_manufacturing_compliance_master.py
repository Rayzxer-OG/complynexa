"""Seed compliance_requirements with manufacturing compliance master entries.

Adds 11 standardized compliance types (compliance_code, compliance_name, description,
default_risk_weight) for each of the 11 core manufacturing industries.
Only inserts if no row with same (industry, compliance_code) exists.

Revision ID: 032
Revises: 031
Create Date: 2025-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "032"
down_revision: Union[str, None] = "031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 11 core manufacturing industries (must match industries table)
MANUFACTURING_INDUSTRIES = [
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

# compliance_code, compliance_name, description, default_risk_weight
COMPLIANCE_MASTER = [
    (
        "FACTORY_LICENSE",
        "Factory License",
        "License from the Directorate of Industrial Safety / Chief Inspector of Factories to establish and operate a factory under the Factories Act.",
        15,
    ),
    (
        "POLLUTION_CTE_CTO",
        "Consent to Establish / Consent to Operate",
        "Consent to Establish (CTE) and Consent to Operate (CTO) from the State Pollution Control Board under Water and Air Acts.",
        15,
    ),
    (
        "FIRE_NOC",
        "Fire NOC",
        "No-Objection Certificate from the Fire Department certifying compliance with fire safety norms.",
        15,
    ),
    (
        "ELECTRICAL_APPROVAL",
        "Electrical Approval",
        "Approval from the Electrical Inspectorate for installation and use of electrical equipment.",
        10,
    ),
    (
        "HAZARDOUS_WASTE",
        "Hazardous Waste Authorization",
        "Authorization for generation, storage, treatment, and disposal of hazardous waste under the Hazardous Waste Rules.",
        20,
    ),
    (
        "MSIHC",
        "MSIHC (Manufacturing, Storage, Import of Hazardous Chemicals)",
        "License or consent for handling hazardous chemicals under the MSIHC rules.",
        20,
    ),
    (
        "PESO_LICENSE",
        "PESO License",
        "License from the Petroleum and Explosives Safety Organization for storage and handling of petroleum and explosives.",
        20,
    ),
    (
        "BOILER_LICENSE",
        "Boiler License",
        "License for installation and operation of boilers from the Boiler Inspectorate.",
        15,
    ),
    (
        "DRUG_LICENSE",
        "Drug Manufacturing License",
        "License from the Drugs Control Authority / CDSCO for manufacture of drugs and cosmetics.",
        20,
    ),
    (
        "FSSAI_LICENSE",
        "FSSAI License",
        "License or registration from the Food Safety and Standards Authority of India for food business operations.",
        15,
    ),
    (
        "EXCISE_LICENSE",
        "Excise License",
        "Central or State excise license for manufacture, storage, or sale of excisable goods (e.g. alcohol, certain chemicals).",
        15,
    ),
]


def upgrade() -> None:
    conn = op.get_bind()
    for industry in MANUFACTURING_INDUSTRIES:
        # Skip industry if it already has any compliance requirements (e.g. from prior seed)
        has_any = conn.execute(
            sa.text(
                "SELECT 1 FROM compliance_requirements WHERE industry = :industry LIMIT 1"
            ),
            {"industry": industry},
        ).scalar()
        if has_any:
            continue
        for code, name, desc, risk in COMPLIANCE_MASTER:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO compliance_requirements
                    (id, compliance_code, industry, compliance_name, description, risk_weight,
                     mandatory, applicability_flag, created_at, updated_at)
                    VALUES (gen_random_uuid(), :code, :industry, :name, :desc, :risk,
                            true, 'M', now(), now())
                    """
                ),
                {
                    "code": code,
                    "industry": industry,
                    "name": name,
                    "desc": desc,
                    "risk": risk,
                },
            )


def downgrade() -> None:
    conn = op.get_bind()
    codes = [c[0] for c in COMPLIANCE_MASTER]
    for industry in MANUFACTURING_INDUSTRIES:
        for code in codes:
            conn.execute(
                sa.text(
                    """
                    DELETE FROM compliance_requirements
                    WHERE industry = :industry AND compliance_code = :code
                    """
                ),
                {"industry": industry, "code": code},
            )
