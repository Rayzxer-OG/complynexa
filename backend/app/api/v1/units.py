"""Unit (factory) creation and management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_user
from app.core.database import get_db
from app.models.compliance_requirement import ComplianceRequirement
from app.models.unit import Unit
from app.models.unit_compliance_attribute import UnitComplianceAttribute
from app.models.user_compliance import UserCompliance
from app.models.unit_escalation_contact import (
    ESCALATION_TRIGGER_CHOICES,
    ESCALATION_TRIGGER_DAYS_CHOICES,
    UnitEscalationContact,
    escalation_trigger_days_to_trigger,
    escalation_trigger_to_days_remaining,
)
from app.models.user import User
from app.api.v1.industries import normalize_and_validate_industry
from app.services.compliance_engine import (
    IndustryNotSupportedError,
    add_conditional_compliance_for_unit,
    get_mapping_for_requirement,
    recalculate_compliance_for_unit,
)
from sqlalchemy.orm import Session

router = APIRouter()


class UnitInfoResponse(BaseModel):
    """Unit details for checklist header and profile edit."""

    organization_name: str
    unit_name: str
    address: str
    state: str
    industry: str | None = None
    employee_count: int | None = None
    hazardous_flag: bool | None = None
    boiler_flag: bool | None = None
    electrical_load: float | None = None
    built_up_area: float | None = None
    spcb_category: str | None = None
    compliance_profile_completed: bool = False

    model_config = {"from_attributes": True}


def _unit_to_info_response(unit: Unit) -> UnitInfoResponse:
    """Build UnitInfoResponse from Unit (include optional profile fields)."""
    return UnitInfoResponse(
        organization_name=unit.organization_name,
        unit_name=unit.unit_name,
        address=unit.address,
        state=unit.state,
        industry=unit.industry,
        employee_count=unit.number_of_employees,
        hazardous_flag=unit.hazardous_flag,
        boiler_flag=unit.boiler_flag,
        electrical_load=unit.connected_load_kw,
        built_up_area=unit.built_up_area,
        spcb_category=unit.spcb_category,
        compliance_profile_completed=getattr(unit, "compliance_profile_completed", False),
    )


class UnitCreateBody(BaseModel):
    organization_name: str = ""
    unit_name: str = ""
    address: str = ""
    state: str = ""
    industry: str = ""
    industry_id: str | None = None  # alias from onboarding/form; persisted as unit.industry
    business_type: str = ""
    employees: int = 0
    manufacturing: bool = False
    electrical_load: float = 0.0


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_unit(
    body: UnitCreateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create a unit and generate its compliance checklist. Industry must be from master (core manufacturing only)."""
    industry_raw = (body.industry or body.industry_id or "").strip()
    industry = normalize_and_validate_industry(db, industry_raw)
    unit = Unit(
        user_id=current_user.id,
        organization_name=body.organization_name,
        unit_name=body.unit_name,
        address=body.address,
        state=body.state,
        industry=industry,
        business_type=body.business_type,
        number_of_employees=body.employees,
        manufacturing=body.manufacturing,
        connected_load_kw=body.electrical_load,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    unit_id_created = unit.id
    return {"ok": True, "message": "Unit created", "unit_id": str(unit_id_created)}


class UnitUpdateBody(BaseModel):
    """Optional unit attributes; only provided fields are updated. Triggers compliance recalc when relevant fields change."""

    industry: str | None = Field(None, min_length=1, max_length=128)
    employee_count: int | None = Field(None, ge=0)
    hazardous_flag: bool | None = None
    boiler_flag: bool | None = None
    electrical_load: float | None = Field(None, ge=0)
    built_up_area: float | None = Field(None, ge=0)
    spcb_category: str | None = Field(None, max_length=64)


@router.patch("/{unit_id}")
def update_unit(
    unit_id: UUID,
    body: UnitUpdateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Update unit attributes. When employee_count, hazardous_flag, boiler_flag, electrical_load, or built_up_area change, compliance is recalculated (new required = Pending, no longer required = Inactive)."""
    unit = db.query(Unit).filter(
        Unit.id == unit_id,
        Unit.user_id == current_user.id,
    ).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    need_recalc = False
    if body.industry is not None and body.industry.strip():
        industry = normalize_and_validate_industry(db, body.industry.strip())
        if unit.industry != industry:
            unit.industry = industry
            need_recalc = True
    if body.employee_count is not None and unit.number_of_employees != body.employee_count:
        unit.number_of_employees = body.employee_count
        need_recalc = True
    if body.hazardous_flag is not None and unit.hazardous_flag != body.hazardous_flag:
        unit.hazardous_flag = body.hazardous_flag
        need_recalc = True
    if body.boiler_flag is not None and unit.boiler_flag != body.boiler_flag:
        unit.boiler_flag = body.boiler_flag
        need_recalc = True
    if body.electrical_load is not None and unit.connected_load_kw != body.electrical_load:
        unit.connected_load_kw = body.electrical_load
        need_recalc = True
    if body.built_up_area is not None and unit.built_up_area != body.built_up_area:
        unit.built_up_area = body.built_up_area
        need_recalc = True
    if body.spcb_category is not None and unit.spcb_category != body.spcb_category:
        unit.spcb_category = body.spcb_category
        need_recalc = True
    db.commit()
    recalc_result = {"added": 0, "marked_inactive": 0}
    if need_recalc:
        try:
            recalc_result = recalculate_compliance_for_unit(db, unit_id)
        except IndustryNotSupportedError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": e.code, "message": str(e)},
            )
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if unit:
            unit.compliance_matrix_generated = True
            db.commit()
    return {"ok": True, "unit_id": str(unit_id), "compliance_recalculated": need_recalc, "recalc": recalc_result}


@router.get("/{unit_id}", response_model=UnitInfoResponse)
def get_unit(
    unit_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UnitInfoResponse:
    """Get unit details by ID. Returns 404 if not found or not owned."""
    unit = db.query(Unit).filter(
        Unit.id == unit_id,
        Unit.user_id == current_user.id,
    ).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    return _unit_to_info_response(unit)


class ActivationStatusResponse(BaseModel):
    """Compliance activation progress for the unit."""
    registration_completed: bool = True
    compliance_profile_completed: bool = False
    compliance_matrix_generated: bool = False
    monitoring_active: bool = False


@router.get("/{unit_id}/activation-status", response_model=ActivationStatusResponse)
def get_activation_status(
    unit_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivationStatusResponse:
    """Return compliance activation progress: registration, profile, matrix, monitoring."""
    unit = db.query(Unit).filter(
        Unit.id == unit_id,
        Unit.user_id == current_user.id,
    ).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    return ActivationStatusResponse(
        registration_completed=True,
        compliance_profile_completed=getattr(unit, "compliance_profile_completed", False),
        compliance_matrix_generated=getattr(unit, "compliance_matrix_generated", False),
        monitoring_active=getattr(unit, "monitoring_active", False),
    )


class EscalationContactItem(BaseModel):
    level: int = Field(..., ge=1, le=3)
    name: str = Field(..., min_length=1, max_length=256)
    email: str = Field(..., max_length=255)
    mobile: str | None = Field(None, max_length=32)
    escalation_trigger: str | None = Field(None, max_length=64)
    escalation_trigger_days: int | None = Field(None)  # 30, 15, 7, 3, or 0 (on expiry). Preferred over escalation_trigger.


class EscalationContactsBody(BaseModel):
    contacts: list[EscalationContactItem] = Field(..., max_length=3)


@router.get("/{unit_id}/escalation-contacts")
def list_escalation_contacts(
    unit_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """List escalation contacts for a unit."""
    unit = db.query(Unit).filter(
        Unit.id == unit_id,
        Unit.user_id == current_user.id,
    ).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    rows = db.query(UnitEscalationContact).filter(UnitEscalationContact.unit_id == unit_id).order_by(UnitEscalationContact.level).all()
    return [
        {
            "level": c.level,
            "name": c.name,
            "email": c.email,
            "mobile": c.mobile,
            "escalation_trigger": c.escalation_trigger,
            "escalation_trigger_days": c.escalation_trigger_days,
        }
        for c in rows
    ]


class ProfileAttributeItem(BaseModel):
    """One compliance profile answer: compliance_requirement_id + applies (for POST profile)."""
    compliance_requirement_id: UUID
    applies: bool


class ComplianceProfileBody(BaseModel):
    """Payload for POST /units/{unit_id}/compliance-attributes when submitting profile (no unit_id in body)."""
    attributes: list[ProfileAttributeItem] = Field(..., max_length=100)


@router.post("/{unit_id}/compliance-profile", status_code=status.HTTP_200_OK)
def save_compliance_profile(
    unit_id: UUID,
    body: ComplianceProfileBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Save compliance profile (conditional answers by compliance_requirement_id). Sets compliance_profile_completed=True.
    Body: { attributes: [{ compliance_requirement_id, applies }, ...] }. Unit id is in path only."""
    unit = db.query(Unit).filter(
        Unit.id == unit_id,
        Unit.user_id == current_user.id,
    ).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    for item in body.attributes:
        req = db.query(ComplianceRequirement).filter(
            ComplianceRequirement.id == item.compliance_requirement_id,
        ).first()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compliance requirement not found",
            )
        mapping = get_mapping_for_requirement(
            db, unit.industry, unit.state, item.compliance_requirement_id,
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
                UnitComplianceAttribute.unit_id == unit_id,
                UnitComplianceAttribute.compliance_requirement_id == item.compliance_requirement_id,
            )
            .first()
        )
        if attr:
            attr.applies = item.applies
        else:
            attr = UnitComplianceAttribute(
                unit_id=unit_id,
                compliance_requirement_id=item.compliance_requirement_id,
                applies=item.applies,
            )
            db.add(attr)
        if item.applies:
            add_conditional_compliance_for_unit(
                db,
                current_user.id,
                unit_id,
                item.compliance_requirement_id,
                req.compliance_name,
            )
        else:
            uc = (
                db.query(UserCompliance)
                .filter(
                    UserCompliance.unit_id == unit_id,
                    UserCompliance.compliance_requirement_id == item.compliance_requirement_id,
                )
                .first()
            )
            if uc:
                db.delete(uc)
    db.commit()
    try:
        recalculate_compliance_for_unit(db, unit_id)
    except IndustryNotSupportedError:
        pass
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if unit:
        unit.compliance_profile_completed = True
        db.commit()
        db.refresh(unit)
    return {"ok": True, "count": len(body.attributes), "compliance_profile_completed": True}


@router.put("/{unit_id}/escalation-contacts")
def save_escalation_contacts(
    unit_id: UUID,
    body: EscalationContactsBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Replace all escalation contacts for a unit. Level 1 (Primary) is required."""
    unit = db.query(Unit).filter(
        Unit.id == unit_id,
        Unit.user_id == current_user.id,
    ).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    level_1 = [c for c in body.contacts if c.level == 1]
    if not level_1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one Level 1 (Primary Compliance Owner) contact is required",
        )
    db.query(UnitEscalationContact).filter(UnitEscalationContact.unit_id == unit_id).delete()
    for c in body.contacts:
        if c.escalation_trigger_days is not None:
            if c.escalation_trigger_days not in ESCALATION_TRIGGER_DAYS_CHOICES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid escalation_trigger_days. Must be one of: {list(ESCALATION_TRIGGER_DAYS_CHOICES)}",
                )
            trigger = escalation_trigger_days_to_trigger(c.escalation_trigger_days)
            trigger_days = c.escalation_trigger_days
        elif c.escalation_trigger:
            if c.escalation_trigger not in ESCALATION_TRIGGER_CHOICES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid escalation_trigger. Must be one of: {ESCALATION_TRIGGER_CHOICES}",
                )
            trigger = c.escalation_trigger
            trigger_days = escalation_trigger_to_days_remaining(c.escalation_trigger)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either escalation_trigger or escalation_trigger_days",
            )
        db.add(
            UnitEscalationContact(
                unit_id=unit_id,
                level=c.level,
                name=c.name.strip(),
                email=c.email.strip(),
                mobile=c.mobile.strip() if c.mobile else None,
                escalation_trigger=trigger,
                escalation_trigger_days=trigger_days,
            )
        )
    db.commit()
    return {"ok": True, "count": len(body.contacts)}
