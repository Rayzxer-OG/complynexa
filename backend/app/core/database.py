"""Database connection and session management."""

import json
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# #region agent log
def _db_debug_log(message: str, data: dict | None = None, hypothesis_id: str = "get_db") -> None:
    try:
        log_path = Path(__file__).resolve().parent.parent.parent / "debug-b9c4c0.log"
        payload = {"sessionId": "b9c4c0", "hypothesisId": hypothesis_id, "location": "database.py:get_db", "message": message, "data": data or {}, "timestamp": __import__("time").time() * 1000}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass
# #endregion


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session and closes it after use."""
    # #region agent log
    _db_debug_log("get_db entered", {}, "H1")
    # #endregion
    db = None
    try:
        db = SessionLocal()
        # #region agent log
        _db_debug_log("SessionLocal() ok", {}, "H1")
        # #endregion
        yield db
        # #region agent log
        _db_debug_log("get_db after yield", {}, "H1")
        # #endregion
    except Exception as e:
        # #region agent log
        _db_debug_log("get_db exception", {"type": type(e).__name__, "msg": str(e)}, "H1")
        # #endregion
        raise
    finally:
        if db is not None:
            db.close()
