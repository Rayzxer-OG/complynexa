#!/usr/bin/env python3
"""Backfill industry_compliance_mapping from compliance_requirements. Run from backend: python scripts/seed_industry_compliance_mapping.py"""

import sys
from pathlib import Path

backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend))


def main() -> int:
    from app.core.database import SessionLocal
    from app.models.compliance_requirement import ComplianceRequirement
    from app.models.industry_compliance_mapping import IndustryComplianceMapping

    db = SessionLocal()
    try:
        existing = db.query(IndustryComplianceMapping).count()
        if existing > 0:
            print(f"industry_compliance_mapping already has {existing} rows. Skipping seed.")
            return 0

        requirements = db.query(ComplianceRequirement).all()
        for req in requirements:
            flag = (req.applicability_flag or "M").upper()
            condition_key = None
            condition_question = None
            if flag == "C":
                # Rules: C requires condition_key and condition_question non-null
                condition_key = (req.conditional_question or req.compliance_name or "applies").replace(" ", "_").lower()[:128]
                condition_key = condition_key or "conditional"
                condition_question = (req.conditional_question or f"Does your unit require {req.compliance_name}?").strip() or "Does this apply?"
            mapping = IndustryComplianceMapping(
                industry_id=req.industry,
                compliance_requirement_id=req.id,
                applicability_flag=flag,
                condition_key=condition_key,
                condition_question=condition_question,
                risk_weight=req.risk_weight,
                state_override_possible=False,
                state_id=None,
                override_flag=False,
            )
            db.add(mapping)
        db.commit()
        print(f"Inserted {len(requirements)} industry_compliance_mapping rows.")
        return 0
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
