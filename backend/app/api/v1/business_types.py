"""Business type master API: returns supported business types for registration/compliance."""

from fastapi import APIRouter

router = APIRouter()

# Backend-defined business types (single source of truth for compliance/reporting).
# Can be replaced later with a DB table and seed.
BUSINESS_TYPES = [
    {"id": "Proprietorship", "name": "Proprietorship", "code": "PROP"},
    {"id": "Partnership", "name": "Partnership", "code": "PART"},
    {"id": "Private Limited", "name": "Private Limited", "code": "PVT"},
    {"id": "LLP", "name": "LLP", "code": "LLP"},
    {"id": "Other", "name": "Other", "code": "OTH"},
]


@router.get("")
def list_business_types() -> list[dict]:
    """
    Return supported business types.
    Used by registration form; backend stores business_type_id on unit for compliance/reporting.
    """
    return [
        {
            "business_type_id": bt["id"],
            "business_type_name": bt["name"],
            "business_type_code": bt["code"],
        }
        for bt in BUSINESS_TYPES
    ]
