#!/usr/bin/env python3
"""Seed compliance_requirements with MP industry sample data. Run from backend: python scripts/seed_compliance_requirements.py"""

import sys
from pathlib import Path

backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend))


def main() -> int:
    from app.core.database import SessionLocal
    from app.models.compliance_requirement import ComplianceRequirement

    db = SessionLocal()
    try:
        existing = db.query(ComplianceRequirement).count()
        if existing > 0:
            print(f"compliance_requirements already has {existing} rows. Skipping seed.")
            return 0

        rows = [
            # Pharmaceutical
            ComplianceRequirement(
                industry="Pharmaceutical",
                compliance_name="Factory License",
                issuing_authority="Directorate of Industrial Safety",
                mandatory=True,
            ),
            ComplianceRequirement(
                industry="Pharmaceutical",
                compliance_name="MP Pollution Control Board Consent to Establish",
                issuing_authority="MP Pollution Control Board",
                mandatory=True,
            ),
            ComplianceRequirement(
                industry="Pharmaceutical",
                compliance_name="MP Pollution Control Board Consent to Operate",
                issuing_authority="MP Pollution Control Board",
                mandatory=True,
            ),
            ComplianceRequirement(
                industry="Pharmaceutical",
                compliance_name="Drug Manufacturing License",
                issuing_authority="Drugs Control Authority",
                mandatory=True,
            ),
            ComplianceRequirement(
                industry="Pharmaceutical",
                compliance_name="Fire NOC",
                issuing_authority="Fire Department",
                mandatory=True,
            ),
            ComplianceRequirement(
                industry="Pharmaceutical",
                compliance_name="Electrical Safety Certificate",
                issuing_authority="Electrical Inspectorate",
                mandatory=True,
            ),
            # Chemical
            ComplianceRequirement(
                industry="Chemical",
                compliance_name="Factory License",
                issuing_authority="Directorate of Industrial Safety",
                mandatory=True,
            ),
            ComplianceRequirement(
                industry="Chemical",
                compliance_name="MPCB Consent",
                issuing_authority="MP Pollution Control Board",
                mandatory=True,
            ),
            ComplianceRequirement(
                industry="Chemical",
                compliance_name="Hazardous Chemical Storage License",
                issuing_authority="Directorate of Industrial Safety",
                mandatory=True,
            ),
            ComplianceRequirement(
                industry="Chemical",
                compliance_name="Fire NOC",
                issuing_authority="Fire Department",
                mandatory=True,
            ),
            ComplianceRequirement(
                industry="Chemical",
                compliance_name="Electrical Safety",
                issuing_authority="Electrical Inspectorate",
                mandatory=True,
            ),
            # Food
            ComplianceRequirement(
                industry="Food",
                compliance_name="Factory License",
                issuing_authority="Directorate of Industrial Safety",
                mandatory=True,
            ),
            ComplianceRequirement(
                industry="Food",
                compliance_name="FSSAI License",
                issuing_authority="FSSAI",
                mandatory=True,
            ),
            ComplianceRequirement(
                industry="Food",
                compliance_name="MPCB Consent",
                issuing_authority="MP Pollution Control Board",
                mandatory=True,
            ),
            ComplianceRequirement(
                industry="Food",
                compliance_name="Fire NOC",
                issuing_authority="Fire Department",
                mandatory=True,
            ),
        ]
        for r in rows:
            db.add(r)
        db.commit()
        print(f"Inserted {len(rows)} compliance requirements.")
        return 0
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
