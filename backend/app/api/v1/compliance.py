"""Compliance checklist API."""

from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ValidationError
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_current_user
from app.core.database import get_db
from app.models.compliance_requirement import ComplianceRequirement
from app.models.document import Document
from app.models.unit import Unit
from app.models.unit_compliance_attribute import UnitComplianceAttribute
from app.models.user import User
from app.models.user_compliance import UserCompliance
from app.services.compliance_engine import (
    IndustryNotSupportedError,
    add_conditional_compliance_for_unit,
    get_effective_mappings_for_industry_state,
    get_mapping_for_requirement,
    get_required_compliance_requirement_ids,
    recalculate_compliance_for_unit,
)
from app.services.compliance_risk_scoring import compute_compliance_score

router = APIRouter()

PROFILE_SETUP_REQUIRED_CODE = "PROFILE_SETUP_REQUIRED"
PROFILE_SETUP_REQUIRED_MSG = "Complete Compliance Profile Setup to activate compliance monitoring."


def _raise_profile_setup_required() -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": PROFILE_SETUP_REQUIRED_CODE, "message": PROFILE_SETUP_REQUIRED_MSG},
    )


def _compute_status(doc: Document | None) -> tuple[str, str | None]:
    """Return (status, expiry_date_iso). expiry_date_iso is None if no doc or doc.expiry_date is None."""
    if doc is None:
        return "pending", None
    expiry = doc.expiry_date
    if expiry is None:
        return "uploaded", None
    today = date.today()
    threshold = today + timedelta(days=30)
    if expiry < today:
        return "expired", expiry.isoformat()
    if expiry <= threshold:
        return "expiring_soon", expiry.isoformat()
    return "valid", expiry.isoformat()


def _applicability_for_requirement(
    db: Session,
    industry_id: str,
    state_id: str | None,
    compliance_requirement_id: UUID,
    req: ComplianceRequirement | None,
) -> str:
    """Resolve applicability flag from mapping only. M/O/C from mapping; no mapping = O for display fallback."""
    mapping = get_mapping_for_requirement(db, industry_id, state_id, compliance_requirement_id)
    if mapping is not None and (mapping.applicability_flag or "").strip().upper() in ("M", "O", "C"):
        return (mapping.applicability_flag or "").strip().upper()
    return "O"


def _risk_weight_for_requirement(
    db: Session,
    industry_id: str,
    state_id: str | None,
    compliance_requirement_id: UUID,
    req: ComplianceRequirement | None,
) -> int:
    """Resolve risk_weight for weighted compliance scoring: mapping first, then requirement, else 0. For internal use."""
    mapping = get_mapping_for_requirement(db, industry_id, state_id, compliance_requirement_id)
    if mapping is not None and mapping.risk_weight is not None:
        return mapping.risk_weight
    if req is not None and req.risk_weight is not None:
        return req.risk_weight
    return 0


def _require_manufacturing_unit(db: Session, unit: Unit) -> None:
    """Raise HTTPException 400 INDUSTRY_NOT_SUPPORTED if unit's industry is not in manufacturing list."""
    try:
        get_required_compliance_requirement_ids(db, unit)
    except IndustryNotSupportedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": str(e)},
        )


@router.get("/dashboard/{unit_id}")
def get_compliance_dashboard(
    unit_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return compliance dashboard for a unit: risk score 0–100 and breakdown."""
    unit = db.query(Unit).filter(Unit.id == unit_id, Unit.user_id == current_user.id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    if not getattr(unit, "compliance_profile_completed", False):
        _raise_profile_setup_required()
    _require_manufacturing_unit(db, unit)
    result = compute_compliance_score(db, unit_id, current_user.id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    return result


@router.get("/checklist/{unit_id}")
def get_checklist(
    unit_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Return compliance checklist for a unit with status derived from latest document expiry."""
    unit = db.query(Unit).filter(Unit.id == unit_id, Unit.user_id == current_user.id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    if not getattr(unit, "compliance_profile_completed", False):
        _raise_profile_setup_required()
    _require_manufacturing_unit(db, unit)
    if not getattr(unit, "monitoring_active", False):
        unit.monitoring_active = True
        db.commit()
    rows = (
        db.query(UserCompliance)
        .options(joinedload(UserCompliance.compliance_requirement))
        .filter(
            UserCompliance.unit_id == unit_id,
            UserCompliance.user_id == current_user.id,
            UserCompliance.status != "inactive",
        )
        .all()
    )
    result = []
    for uc in rows:
        doc = (
            db.query(Document)
            .filter(
                Document.user_id == current_user.id,
                Document.unit_id == unit_id,
                Document.compliance_requirement_id == uc.compliance_requirement_id,
            )
            .order_by(Document.created_at.desc())
            .first()
        )
        status_val, expiry_date_iso = _compute_status(doc)
        req = uc.compliance_requirement
        applicability_flag = _applicability_for_requirement(
            db, unit.industry, unit.state, uc.compliance_requirement_id, req
        )
        risk_weight = _risk_weight_for_requirement(
            db, unit.industry, unit.state, uc.compliance_requirement_id, req
        )
        item = {
            "compliance_requirement_id": str(uc.compliance_requirement_id),
            "compliance_name": uc.compliance_name,
            "description": (req.description if req else None),
            "issuing_authority": (doc.issuing_authority if doc else None) or (req.issuing_authority if req else None),
            "status": status_val,
            "expiry_date": expiry_date_iso,
            "license_number": doc.license_number if doc else None,
            "issue_date": doc.issue_date.isoformat() if doc and doc.issue_date else None,
            "applicability_flag": applicability_flag,
            "risk_weight": risk_weight,
        }
        # For conditional (C) items: expose why this is required (condition question + user response from UnitComplianceAttribute)
        if applicability_flag == "C":
            mapping = get_mapping_for_requirement(
                db, unit.industry, unit.state, uc.compliance_requirement_id
            )
            attr = (
                db.query(UnitComplianceAttribute)
                .filter(
                    UnitComplianceAttribute.unit_id == unit_id,
                    UnitComplianceAttribute.compliance_requirement_id == uc.compliance_requirement_id,
                )
                .first()
            )
            question = None
            if mapping and (mapping.condition_question or "").strip():
                question = (mapping.condition_question or "").strip()
            if not question and req and (req.conditional_question or "").strip():
                question = (req.conditional_question or "").strip()
            if not question and req:
                question = f"Does this unit require {req.compliance_name}?"
            if question:
                item["required_because"] = {
                    "condition_question": question,
                    "user_response": "Yes" if (attr and attr.applies) else "No",
                }
        result.append(item)
    return result


@router.get("/conditional-questions/{unit_id}")
def get_conditional_questions(
    unit_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Return conditional (C) compliance questions for the unit. Mapping table only: only C rows for this industry."""
    unit = db.query(Unit).filter(Unit.id == unit_id, Unit.user_id == current_user.id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    answered_ids = {
        row.compliance_requirement_id
        for row in db.query(UnitComplianceAttribute.compliance_requirement_id).filter(
            UnitComplianceAttribute.unit_id == unit_id,
        ).all()
    }
    mappings = get_effective_mappings_for_industry_state(db, unit.industry, unit.state)
    mappings_c = [
        m for m in mappings
        if (m.applicability_flag or "").strip().upper() == "C"
    ]
    requirements = [m.compliance_requirement for m in mappings_c if m.compliance_requirement]
    requirements = [r for r in requirements if r.id not in answered_ids]
    return [
        {
            "compliance_requirement_id": str(req.id),
            "compliance_name": req.compliance_name,
            "conditional_question": (
                req.conditional_question
                or f"Does this unit require {req.compliance_name}?"
            ),
        }
        for req in requirements
    ]


class ComplianceAttributeItem(BaseModel):
    compliance_requirement_id: UUID
    applies: bool


class ComplianceAttributeBulk(BaseModel):
    unit_id: UUID
    attributes: list[ComplianceAttributeItem]


async def save_compliance_attributes(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Bulk upsert user Yes/No answers for conditional compliances in a single transaction.
    Payload: { unit_id, attributes: [{ compliance_requirement_id, applies }, ...] }.
    Registered in main.py so body is always parsed as ComplianceAttributeBulk (not single-item)."""
    body_bytes = await request.body()
    try:
        payload = ComplianceAttributeBulk.model_validate_json(body_bytes.decode("utf-8"))
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid JSON body. Expected {{ unit_id: UUID, attributes: [{{ compliance_requirement_id, applies }}, ...] }}. {e!s}",
        )
    unit = db.query(Unit).filter(Unit.id == payload.unit_id, Unit.user_id == current_user.id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    _require_manufacturing_unit(db, unit)
    for item in payload.attributes:
        req = db.query(ComplianceRequirement).filter(ComplianceRequirement.id == item.compliance_requirement_id).first()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compliance requirement not found",
            )
        mapping = get_mapping_for_requirement(
            db, unit.industry, unit.state, item.compliance_requirement_id
        )
        is_conditional = (mapping and (mapping.applicability_flag or "").upper() == "C") or (
            not mapping and (req.applicability_flag or "").upper() == "C"
        )
        if not is_conditional:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not a conditional compliance",
            )
        attr = (
            db.query(UnitComplianceAttribute)
            .filter(
                UnitComplianceAttribute.unit_id == payload.unit_id,
                UnitComplianceAttribute.compliance_requirement_id == item.compliance_requirement_id,
            )
            .first()
        )
        if attr:
            attr.applies = item.applies
        else:
            attr = UnitComplianceAttribute(
                unit_id=payload.unit_id,
                compliance_requirement_id=item.compliance_requirement_id,
                applies=item.applies,
            )
            db.add(attr)
        if item.applies:
            add_conditional_compliance_for_unit(
                db,
                current_user.id,
                payload.unit_id,
                item.compliance_requirement_id,
                req.compliance_name,
            )
        else:
            uc = (
                db.query(UserCompliance)
                .filter(
                    UserCompliance.unit_id == payload.unit_id,
                    UserCompliance.compliance_requirement_id == item.compliance_requirement_id,
                )
                .first()
            )
            if uc:
                db.delete(uc)
    db.commit()
    recalc = recalculate_compliance_for_unit(db, payload.unit_id)
    unit.compliance_profile_completed = True
    db.commit()
    return {"ok": True, "count": len(payload.attributes), "recalc": recalc}


@router.get("/document/{compliance_requirement_id}")
def get_compliance_document(
    compliance_requirement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return the uploaded document for this compliance requirement, if any (for current user)."""
    doc = (
        db.query(Document)
        .filter(
            Document.user_id == current_user.id,
            Document.compliance_requirement_id == compliance_requirement_id,
        )
        .order_by(Document.created_at.desc())
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No document uploaded for this compliance")
    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "document_name": doc.document_name,
        "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
        "created_at": doc.created_at.isoformat(),
    }