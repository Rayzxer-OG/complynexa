"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()


@router.get("")
def health_check() -> dict:
    """Basic liveness check (no database)."""
    return {"status": "ok", "service": "Compliance Tracker"}


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)) -> dict:
    """Readiness check including database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {
            "status": "degraded",
            "database": "disconnected",
            "error": str(e),
            "hint": "Check PostgreSQL is running and DATABASE_URL in backend/.env (e.g. postgresql://postgres:postgres@localhost:5432/compliance_tracker). Create DB: createdb compliance_tracker",
        }
