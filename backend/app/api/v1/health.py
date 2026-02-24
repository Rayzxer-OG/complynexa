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
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
    }
