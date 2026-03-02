"""Auth API endpoints."""

import json
import logging
import traceback
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.v1.industries import normalize_and_validate_industry
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.unit import Unit
from app.models.user import User
from app.schemas.auth import OnboardingBody, TokenResponse, UserLogin, UserRegister
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Log in backend folder regardless of cwd (auth.py -> v1 -> api -> app -> backend)
DEBUG_LOG = Path(__file__).resolve().parent.parent.parent.parent / "debug-b9c4c0.log"


def _debug_log(message: str, data: dict, hypothesis_id: str) -> None:
    try:
        payload = {
            "sessionId": "b9c4c0",
            "location": "auth.py:register",
            "message": message,
            "data": data,
            "hypothesisId": hypothesis_id,
            "timestamp": __import__("time").time() * 1000,
        }
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass


def _format_register_error(e: Exception) -> str:
    """Build a clear error message for the client."""
    msg = f"{type(e).__name__}: {str(e)}"
    if "password_hash" in msg.lower() or "column" in msg.lower():
        msg += " Run: alembic upgrade head in the backend folder, then restart the server."
    return msg


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    body: UserRegister,
    db: Session = Depends(get_db),
):
    """Register a new user with email, password, and full_name."""
    # #region agent log
    _debug_log("register entry", {"email": body.email}, "H4")
    # #endregion
    try:
        logger.info("Register attempt for email=%s", body.email)
        # #region agent log
        _debug_log("before email check query", {"email": body.email}, "H1")
        # #endregion
        if db.query(User).filter(User.email == body.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        # #region agent log
        _debug_log("after email check, before hash_password", {}, "H2")
        # #endregion
        hashed = hash_password(body.password)
        # #region agent log
        _debug_log("after hash_password", {"hash_len": len(hashed)}, "H3")
        # #endregion
        user = User(
            email=body.email,
            full_name=body.full_name,
            password_hash=hashed,
        )
        db.add(user)
        # #region agent log
        _debug_log("before commit", {}, "H2")
        # #endregion
        db.commit()
        db.refresh(user)
        # #region agent log
        _debug_log("after commit success", {"user_id": str(user.id)}, "H1")
        # #endregion
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        # #region agent log
        _debug_log(
            "register exception",
            {"exc_type": type(e).__name__, "exc_msg": str(e)[:200]},
            "H3",
        )
        # #endregion
        db.rollback()
        logger.exception("Register failed: %s", traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": _format_register_error(e), "type": type(e).__name__},
        )


@router.post("/onboarding", status_code=status.HTTP_201_CREATED)
def onboarding(body: OnboardingBody, db: Session = Depends(get_db)) -> dict:
    """Create organization/unit and admin user in one step. Returns organization_id, unit_id, access_token."""
    try:
        if db.query(User).filter(User.email == body.user.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        hashed = hash_password(body.user.password)
        user = User(
            email=body.user.email,
            full_name=body.user.full_name,
            password_hash=hashed,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        org = body.organization
        industry = normalize_and_validate_industry(db, org.industry_id or "")
        unit = Unit(
            user_id=user.id,
            organization_name=org.organization_name,
            unit_name=org.unit_name,
            address=org.address,
            state=org.state,
            industry=industry,
            business_type=org.business_type_id or "",
            number_of_employees=org.employees,
            manufacturing=org.manufacturing,
            connected_load_kw=org.electrical_load,
        )
        db.add(unit)
        db.commit()
        db.refresh(unit)

        access_token = create_access_token(user.id)
        return {
            "organization_id": str(unit.id),
            "unit_id": str(unit.id),
            "access_token": access_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Onboarding failed: %s", traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": _format_register_error(e), "type": type(e).__name__},
        )


@router.post("/login", response_model=TokenResponse)
def login(
    body: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Login with email and password; returns JWT access token."""
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
        )
    access_token = create_access_token(user.id)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    """Return current authenticated user info."""
    return current_user
