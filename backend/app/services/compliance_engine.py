"""Compliance applicability engine: generates required checklist per unit from master rules.

Mapping table is the single source of truth. No fallback to compliance_requirements.applicability_flag.

- M (Mandatory): always include in checklist; do not ask questions.
- O (Optional): include in checklist.
- C (Conditional): ask question; include only if UnitComplianceAttribute.applies == True.
- "-" / blank / null: not applicable for that industry; do not show, do not ask.
"""

import logging
from uuid import UUID

logger = logging.getLogger(__name__)

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.compliance_requirement import ComplianceRequirement
from app.models.industry import Industry
from app.models.industry_compliance_mapping import IndustryComplianceMapping
from app.models.unit import Unit


class IndustryNotSupportedError(Exception):
    """Raised when compliance generation or recalc is requested for a non-manufacturing industry. MVP supports manufacturing only."""
    def __init__(self, industry_id: str) -> None:
        self.industry_id = industry_id
        self.code = "INDUSTRY_NOT_SUPPORTED"
        super().__init__(f"Industry not supported: {industry_id}. Complynexa MVP is restricted to manufacturing industries only.")


def _require_manufacturing_industry(db: Session, industry_id: str) -> None:
    """Raise IndustryNotSupportedError if industry_id is not in the industries table (manufacturing only)."""
    if not industry_id or not str(industry_id).strip():
        raise IndustryNotSupportedError(industry_id or "")
    key = str(industry_id).strip().lower()
    exists = db.query(Industry).filter(func.lower(Industry.industry_id) == key).first()
    if not exists:
        raise IndustryNotSupportedError(str(industry_id).strip())
from app.models.unit_compliance_attribute import UnitComplianceAttribute
from app.models.user_compliance import UserCompliance

# Only these applicability flags from mapping are included. "-", blank, null = not applicable.
APPLICABILITY_INCLUDE = frozenset({"M", "O", "C"})


def _normalize_applicability(flag: str | None) -> str | None:
    """Return 'M', 'O', or 'C' if applicable; else None (not applicable / ignore)."""
    if flag is None:
        return None
    v = (flag or "").strip().upper()
    if v in APPLICABILITY_INCLUDE:
        return v
    return None


def _get_unit_conditional_applies_requirement_ids(db: Session, unit_id: UUID) -> set[UUID]:
    """
    Return set of compliance_requirement_id for which the unit has answered Yes (applies=True).
    Used for C (conditional) applicability: include only if requirement is in this set.
    """
    rows = (
        db.query(UnitComplianceAttribute.compliance_requirement_id)
        .filter(
            UnitComplianceAttribute.unit_id == unit_id,
            UnitComplianceAttribute.applies.is_(True),
        )
        .all()
    )
    return {r[0] for r in rows}

USER_COMPLIANCE_STATUS_ACTIVE = ("pending", "uploaded", "valid", "expiring_soon", "expired")
USER_COMPLIANCE_STATUS_INACTIVE = "inactive"


def get_effective_mappings_for_industry_state(
    db: Session, industry_id: str, state_id: str | None
) -> list[IndustryComplianceMapping]:
    """
    Resolve industry_compliance_mapping with state-level override.

    a) Check mapping where industry_id + state_id match (state-specific rows).
    b) If none found, fallback to industry-level default mapping (industry_id match, state_id IS NULL).

    Compliance checklist API and all consumers use this so state-specific mapping is respected.
    """
    industry_key = (industry_id or "").strip().lower()
    if state_id and state_id.strip():
        state_specific = (
            db.query(IndustryComplianceMapping)
            .options(joinedload(IndustryComplianceMapping.compliance_requirement))
            .filter(
                func.lower(IndustryComplianceMapping.industry_id) == industry_key,
                IndustryComplianceMapping.state_id == state_id.strip(),
            )
            .all()
        )
        if state_specific:
            return state_specific
    default = (
        db.query(IndustryComplianceMapping)
        .options(joinedload(IndustryComplianceMapping.compliance_requirement))
        .filter(
            func.lower(IndustryComplianceMapping.industry_id) == industry_key,
            IndustryComplianceMapping.state_id.is_(None),
        )
        .all()
    )
    return default


def get_mapping_for_requirement(
    db: Session, industry_id: str, state_id: str | None, compliance_requirement_id: UUID
) -> IndustryComplianceMapping | None:
    """Resolve single mapping: state-specific first, then industry default."""
    industry_key = (industry_id or "").strip().lower()
    if state_id and state_id.strip():
        m = (
            db.query(IndustryComplianceMapping)
            .filter(
                func.lower(IndustryComplianceMapping.industry_id) == industry_key,
                IndustryComplianceMapping.state_id == state_id.strip(),
                IndustryComplianceMapping.compliance_requirement_id == compliance_requirement_id,
            )
            .first()
        )
        if m is not None:
            return m
    return (
        db.query(IndustryComplianceMapping)
        .filter(
            func.lower(IndustryComplianceMapping.industry_id) == industry_key,
            IndustryComplianceMapping.state_id.is_(None),
            IndustryComplianceMapping.compliance_requirement_id == compliance_requirement_id,
        )
        .first()
    )


def get_required_compliance_requirement_ids(db: Session, unit: Unit) -> set[UUID]:
    """
    Return the set of compliance_requirement_id for this unit. Mapping table only:
    - M: include (mandatory)
    - O: include (optional)
    - C: include only if UnitComplianceAttribute.applies == True
    - "-" / null / other: ignore (not applicable)
    No fallback to compliance_requirements table.
    """
    industry = unit.industry
    _require_manufacturing_industry(db, industry)
    state_id = getattr(unit, "state", None) or None
    conditional_applies_ids = _get_unit_conditional_applies_requirement_ids(db, unit.id)
    result: set[UUID] = set()
    mappings = get_effective_mappings_for_industry_state(db, industry, state_id)
    for m in mappings:
        flag = _normalize_applicability(m.applicability_flag)
        if flag is None:
            continue
        req = m.compliance_requirement
        if not req:
            continue
        if flag == "C":
            if req.id not in conditional_applies_ids:
                continue
        result.add(req.id)
    return result


def recalculate_compliance_for_unit(db: Session, unit_id: UUID) -> dict:
    """
    Re-run compliance applicability for the unit and sync user_compliance.
    Fully driven by mapping + UnitComplianceAttribute (requirement-based only):
    - Newly required: create UserCompliance with status='pending'.
    - No longer required: set status='inactive' (do not delete).
    - Preserve existing documents.
    """
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        return {"added": 0, "marked_inactive": 0}
    required_ids = get_required_compliance_requirement_ids(db, unit)
    active_required = required_ids
    existing_rows = (
        db.query(UserCompliance)
        .filter(UserCompliance.unit_id == unit_id)
        .all()
    )
    existing_ids = {uc.compliance_requirement_id for uc in existing_rows}
    marked_inactive = 0
    for uc in existing_rows:
        if uc.compliance_requirement_id not in active_required:
            if uc.status != USER_COMPLIANCE_STATUS_INACTIVE:
                uc.status = USER_COMPLIANCE_STATUS_INACTIVE
                marked_inactive += 1
    added = 0
    for crid in active_required:
        if crid in existing_ids:
            continue
        req = db.query(ComplianceRequirement).filter(ComplianceRequirement.id == crid).first()
        if not req:
            continue
        uc = UserCompliance(
            user_id=unit.user_id,
            unit_id=unit_id,
            compliance_requirement_id=crid,
            compliance_name=req.compliance_name,
            status="pending",
        )
        db.add(uc)
        added += 1
    db.commit()
    return {"added": added, "marked_inactive": marked_inactive}


def generate_compliance_checklist(
    db: Session,
    industry: str,
    employees: int,
    connected_load_kw: float,
    manufacturing: bool,
    user_id: UUID,
    unit_id: UUID,
    state_id: str | None = None,
) -> list[UserCompliance]:
    """
    Build checklist from industry_compliance_mapping only. No fallback to compliance_requirements.
    - M / O: include; C: include only if UnitComplianceAttribute.applies == True.
    - "-" / null / other: ignore.
    """
    _require_manufacturing_industry(db, industry)
    mappings = get_effective_mappings_for_industry_state(db, industry, state_id)
    conditional_applies_ids = _get_unit_conditional_applies_requirement_ids(db, unit_id)
    created: list[UserCompliance] = []
    for m in mappings:
        flag = _normalize_applicability(m.applicability_flag)
        if flag is None:
            continue
        req = m.compliance_requirement
        if not req:
            continue
        if flag == "C":
            if req.id not in conditional_applies_ids:
                continue
        uc = UserCompliance(
            user_id=user_id,
            unit_id=unit_id,
            compliance_requirement_id=req.id,
            compliance_name=req.compliance_name,
            status="pending",
        )
        db.add(uc)
        created.append(uc)
    db.commit()
    for uc in created:
        db.refresh(uc)
    return created


def add_conditional_compliance_for_unit(
    db: Session,
    user_id: UUID,
    unit_id: UUID,
    compliance_requirement_id: UUID,
    compliance_name: str,
) -> UserCompliance:
    """Add a user_compliance row when user answers Yes to a conditional compliance question."""
    existing = (
        db.query(UserCompliance)
        .filter(
            UserCompliance.unit_id == unit_id,
            UserCompliance.compliance_requirement_id == compliance_requirement_id,
        )
        .first()
    )
    if existing:
        return existing
    uc = UserCompliance(
        user_id=user_id,
        unit_id=unit_id,
        compliance_requirement_id=compliance_requirement_id,
        compliance_name=compliance_name,
        status="pending",
    )
    db.add(uc)
    db.commit()
    db.refresh(uc)
    logger.info(
        "add_conditional_compliance_for_unit: created 1 UserCompliance row for unit_id=%s compliance_requirement_id=%s",
        unit_id,
        compliance_requirement_id,
    )
    return uc