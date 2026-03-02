"""Organization/unit onboarding API (factory details)."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.industries import normalize_and_validate_industry
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.unit import Unit
from app.models.user import User
router = APIRouter()


class OrganizationCreateBody(BaseModel):
    organization_name: str = ""
    unit_name: str = ""
    address: str = ""
    state: str = ""
    industry: str = ""
    business_type: str = ""
    employees: int = 0
    manufacturing: bool = False
    electrical_load: float = 0.0


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_organization(
    body: OrganizationCreateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create unit and generate compliance checklist. Industry must be from master (core manufacturing only)."""
    industry = normalize_and_validate_industry(db, body.industry or "")
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
    return {"ok": True, "message": "Organization details saved", "unit_id": str(unit.id)}
