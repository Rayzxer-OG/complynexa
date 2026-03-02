"""Industry master API: returns core manufacturing industries only (from industries table)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.industry import Industry
from app.models.industry_compliance_mapping import IndustryComplianceMapping

router = APIRouter()


def validate_industry_id(db: Session, industry_id: str) -> None:
    """Raise 400 if industry_id is not in the industries master table (core manufacturing only)."""
    if not industry_id or not industry_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Industry is required. Choose from the supported manufacturing industries.",
        )
    exists = db.query(Industry).filter(Industry.industry_id == industry_id.strip()).first()
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid industry. Only core manufacturing industries are supported.",
        )


# Canonical list for validation; must match industries table (migration 030).
ALLOWED_INDUSTRIES = [
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


def normalize_and_validate_industry(db: Session, industry: str) -> str:
    """
    Normalize industry (strip) and resolve to canonical industry_id from the industries table (case-insensitive).
    Rejects values not in the allowed list. Returns exact canonical value for exact-match safe storage.
    """
    if not industry or not industry.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Industry is required. Choose from the supported manufacturing industries.",
        )
    raw = industry.strip().lower()
    row = db.query(Industry).filter(func.lower(Industry.industry_id) == raw).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid industry. Only core manufacturing industries are supported.",
        )
    canonical = row.industry_id
    print("Normalized industry:", canonical)
    return canonical


def _industry_to_code(name: str) -> str:
    """Derive a short code from industry name for display (e.g. Pharmaceutical -> PHARMA)."""
    if not name:
        return ""
    parts = name.replace("-", " ").split()
    if len(parts) == 1 and len(parts[0]) >= 4:
        return parts[0][:5].upper()
    return "".join(p[0].upper() for p in parts if p)[:8] or name[:8].upper()


def _fetch_conditional_questions(industry_id: str, db: Session) -> list[dict]:
    """Shared logic: return conditional questions for an industry."""
    industry_id = (industry_id or "").strip()
    rows = (
        db.query(
            IndustryComplianceMapping.condition_key,
            IndustryComplianceMapping.condition_question,
            IndustryComplianceMapping.condition_type,
        )
        .filter(
            IndustryComplianceMapping.industry_id == industry_id,
            IndustryComplianceMapping.state_id.is_(None),
            func.upper(IndustryComplianceMapping.applicability_flag) == "C",
            IndustryComplianceMapping.condition_key.isnot(None),
            IndustryComplianceMapping.condition_key != "",
        )
        .distinct()
        .all()
    )
    seen: set[str] = set()
    result = []
    for key, question, cond_type in rows:
        if not key or key.strip() in seen:
            continue
        key = key.strip()
        seen.add(key)
        label = (question.strip() if question and question.strip() else None) or _default_question_for_key(key)
        q_type = (cond_type or "boolean").strip().lower() if cond_type else "boolean"
        if q_type not in ("boolean", "numeric", "select"):
            q_type = "boolean"
        result.append({"condition_key": key, "question": label, "type": q_type})
    result.sort(key=lambda x: x["condition_key"])
    print(f"Industry conditional questions: industry_id={industry_id!r}, count={len(result)}")
    return result


@router.get("/conditional-questions", summary="By query param (preferred)")
def get_industry_conditional_questions_query(
    industry_id: str = Query(..., description="Industry ID, e.g. Pharmaceutical"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Return conditional compliance questions for an industry (query param).
    Same data as path variant; use this if the path variant returns 404.
    """
    return _fetch_conditional_questions(industry_id, db)


@router.get("/conditional-questions/{industry_id}", summary="By path param")
def get_industry_conditional_questions_path(
    industry_id: str,
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Return conditional compliance questions for an industry (path param).
    """
    return _fetch_conditional_questions(industry_id, db)


@router.get("")
def list_industries(db: Session = Depends(get_db)) -> list[dict]:
    """
    Return supported industries from the industries master table only (core manufacturing).
    No generic placeholders (Manufacturing, Other, Retail, Healthcare). Used by registration form.
    """
    rows = db.query(Industry).order_by(Industry.industry_id).all()
    return [
        {
            "industry_id": r.industry_id,
            "industry_name": r.industry_name,
            "industry_code": _industry_to_code(r.industry_name),
        }
        for r in rows
    ]


def _default_question_for_key(condition_key: str) -> str:
    """Human-readable default question when condition_question is not set on mapping."""
    return f"Does your unit have {condition_key.replace('_', ' ')}?"
