#!/usr/bin/env python3
"""
Backfill industry_compliance_mapping with M/C/O matrix and conditional questions (C).

Same logic as alembic migration 033_seed_industry_compliance_mapping_manufacturing.
Run from backend: python scripts/seed_industry_compliance_mapping_manufacturing.py

Requires:
  - alembic upgrade head  (so industry_compliance_mapping has all columns and compliance_requirements exist)
  - compliance_requirements seeded (migration 032) with industry + compliance_code
"""

import sys
from pathlib import Path

backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend))

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


def main() -> int:
    import sqlalchemy as sa
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        # 1) Backfill compliance_code on compliance_requirements so we can resolve by (industry, compliance_code)
        for name, code in BACKFILL_NAME_TO_CODE:
            db.execute(
                sa.text(
                    """
                    UPDATE compliance_requirements
                    SET compliance_code = :code
                    WHERE compliance_code IS NULL AND TRIM(compliance_name) = :name
                    """
                ),
                {"code": code, "name": name.strip()},
            )
        db.commit()

        inserted = 0
        skipped = 0
        no_req = 0
        for industry_id, items in INDUSTRY_MATRIX.items():
            for compliance_code, flag, risk in items:
                row = db.execute(
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
                    no_req += 1
                    continue
                req_id = row[0]
                cond_key = None
                cond_question = None
                if flag == "C" and compliance_code in CONDITION_FOR_C:
                    cond_key, cond_question = CONDITION_FOR_C[compliance_code]
                cond_type = "boolean" if flag == "C" else None

                existing = db.execute(
                    sa.text(
                        """
                        SELECT 1 FROM industry_compliance_mapping
                        WHERE industry_id = :industry_id AND compliance_requirement_id = :req_id AND state_id IS NULL
                        LIMIT 1
                        """
                    ),
                    {"industry_id": industry_id, "req_id": req_id},
                ).scalar()
                if existing:
                    # Update existing row so M/C/O and condition fields match the matrix (fixes old seed that set all M)
                    db.execute(
                        sa.text(
                            """
                            UPDATE industry_compliance_mapping
                            SET applicability_flag = :flag, condition_key = :cond_key,
                                condition_question = :cond_question, condition_type = :cond_type,
                                risk_weight = :risk
                            WHERE industry_id = :industry_id AND compliance_requirement_id = :req_id AND state_id IS NULL
                            """
                        ),
                        {
                            "industry_id": industry_id,
                            "req_id": req_id,
                            "flag": flag,
                            "cond_key": cond_key,
                            "cond_question": cond_question,
                            "cond_type": cond_type,
                            "risk": risk,
                        },
                    )
                    inserted += 1
                else:
                    db.execute(
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
                            "cond_type": cond_type,
                            "risk": risk,
                        },
                    )
                    inserted += 1
        db.commit()
        print(f"Inserted/updated {inserted} rows in industry_compliance_mapping (skipped {skipped} unchanged, {no_req} had no compliance_requirement).")
        if no_req > 0:
            print("  If many 'no compliance_requirement', run: alembic upgrade head  (ensure 032 ran to seed compliance_requirements).")
        return 0
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
