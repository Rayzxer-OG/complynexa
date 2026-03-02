"""Compliance risk scoring: 0–100 score from checklist status and applicability."""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.compliance_requirement import ComplianceRequirement
from app.models.document import Document
from app.models.unit import Unit
from app.models.user_compliance import UserCompliance
from app.services.compliance_engine import get_mapping_for_requirement


def _compute_status(doc: Document | None) -> str:
    """Return status string: pending, uploaded, valid, expiring_soon, expired."""
    if doc is None:
        return "pending"
    expiry = doc.expiry_date
    if expiry is None:
        return "uploaded"
    today = date.today()
    threshold = today + timedelta(days=30)
    if expiry < today:
        return "expired"
    if expiry <= threshold:
        return "expiring_soon"
    return "valid"


def _applicability_for_requirement(
    db: Session,
    industry_id: str,
    state_id: str | None,
    compliance_requirement_id: UUID,
    req: ComplianceRequirement | None,
) -> str:
    """Resolve applicability flag: state-level mapping first, then industry default, else requirement."""
    mapping = get_mapping_for_requirement(db, industry_id, state_id, compliance_requirement_id)
    if mapping is not None:
        return (mapping.applicability_flag or "M").upper()
    return (req.applicability_flag if req else None) or ("M" if req and req.mandatory else "O")


def compute_compliance_score(
    db: Session, unit_id: UUID, user_id: UUID
) -> dict:
    """
    Calculate compliance score 0–100 and breakdown for a unit.

    Score is (compliant_count / total_required) * 100 when total_required > 0, else 100.
    Compliant = status in (valid, uploaded, expiring_soon).

    Returns:
        compliance_score: int 0–100
        total_required: int
        compliant: int
        missing_mandatory: int (M + pending)
        expired: int (any expired)
        conditional_not_fulfilled: int (C + pending or expired)
    """
    unit = db.query(Unit).filter(Unit.id == unit_id, Unit.user_id == user_id).first()
    if not unit:
        return None

    rows = (
        db.query(UserCompliance)
        .options(joinedload(UserCompliance.compliance_requirement))
        .filter(
            UserCompliance.unit_id == unit_id,
            UserCompliance.user_id == user_id,
            UserCompliance.status != "inactive",
        )
        .all()
    )

    total_required = len(rows)
    if total_required == 0:
        return {
            "compliance_score": 100,
            "total_required": 0,
            "compliant": 0,
            "missing_mandatory": 0,
            "expired": 0,
            "conditional_not_fulfilled": 0,
        }

    compliant = 0
    missing_mandatory = 0
    expired_count = 0
    conditional_not_fulfilled = 0

    for uc in rows:
        doc = (
            db.query(Document)
            .filter(
                Document.user_id == user_id,
                Document.unit_id == unit_id,
                Document.compliance_requirement_id == uc.compliance_requirement_id,
            )
            .order_by(Document.created_at.desc())
            .first()
        )
        status_val = _compute_status(doc)
        applicability = _applicability_for_requirement(
            db, unit.industry, unit.state, uc.compliance_requirement_id, uc.compliance_requirement
        )

        if status_val in ("valid", "uploaded", "expiring_soon"):
            compliant += 1
        if applicability == "M" and status_val == "pending":
            missing_mandatory += 1
        if status_val == "expired":
            expired_count += 1
        if applicability == "C" and status_val in ("pending", "expired"):
            conditional_not_fulfilled += 1

    score = round((compliant / total_required) * 100)
    score = max(0, min(100, score))

    return {
        "compliance_score": score,
        "total_required": total_required,
        "compliant": compliant,
        "missing_mandatory": missing_mandatory,
        "expired": expired_count,
        "conditional_not_fulfilled": conditional_not_fulfilled,
    }
