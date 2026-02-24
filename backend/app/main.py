"""Compliance Tracker - FastAPI application entry point."""
import json
import logging
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.email_service import send_email_reminder
from app.services.reminder_service import get_documents_requiring_reminder

logger = logging.getLogger(__name__)
settings = get_settings()


def run_daily_reminder_check() -> None:
    """Run reminder check: find documents due for reminder and send emails. Uses its own DB session."""
    db = SessionLocal()
    try:
        documents = get_documents_requiring_reminder(db)
        for document in documents:
            try:
                send_email_reminder(document, db)
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Reminder send failed for document %s", document.id)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    # #region agent log — write at startup so we know this process has our code and where log goes
    try:
        _log_path = _debug_log_path()
        with open(_log_path, "a", encoding="utf-8") as _f:
            _f.write(json.dumps({"sessionId": "b9c4c0", "message": "startup", "location": "main.py:lifespan", "data": {"path": str(_log_path)}, "timestamp": int(time.time() * 1000)}) + "\n")
        import sys
        print(f"[DEBUG] Log file: {_log_path}", file=sys.stderr)
    except Exception as _e:
        import sys
        print(f"[DEBUG] Failed to write log file: {_e}", file=sys.stderr)
    # #endregion
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_daily_reminder_check,
        CronTrigger(hour=9, minute=0),
        id="daily_reminder",
    )
    scheduler.start()
    logger.info("Scheduler started: daily reminder at 09:00")
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


app = FastAPI(
    title=settings.app_name,
    description="SaaS backend for compliance tracking.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# #region agent log
def _debug_log_path() -> Path:
    import os
    if os.environ.get("DEBUG_LOG_PATH"):
        return Path(os.environ["DEBUG_LOG_PATH"]).resolve() / "debug-b9c4c0.log"
    return Path(__file__).resolve().parent.parent / "debug-b9c4c0.log"


def _main_debug_log(message: str, data: dict | None = None, hypothesis_id: str = "main") -> None:
    try:
        log_path = _debug_log_path()
        payload = {"sessionId": "b9c4c0", "hypothesisId": hypothesis_id, "location": "main.py", "message": message, "data": data or {}, "timestamp": int(time.time() * 1000)}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass
# #endregion


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return 500 with detail in JSON so clients see the real error."""
    try:
        # #region agent log
        _main_debug_log("exception_handler", {"path": request.url.path, "type": type(exc).__name__, "msg": str(exc)}, "H0")
        # #endregion
        logger.exception("Unhandled exception")
        detail = str(exc) or "Internal server error"
        return JSONResponse(
            status_code=500,
            content={
                "detail": detail,
                "type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            },
        )
    except Exception as handler_error:
        logger.exception("Exception in exception handler: %s", handler_error)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": "HandlerError"},
        )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.middleware("http")
async def catch_all_exceptions(request: Request, call_next):
    """Ensure any unhandled exception returns JSON with detail."""
    # #region agent log
    if "register" in request.url.path:
        _main_debug_log("middleware before route", {"path": request.url.path}, "H0")
    # #endregion
    try:
        return await call_next(request)
    except Exception as exc:
        # #region agent log
        if "register" in request.url.path:
            _main_debug_log("middleware caught exception", {"path": request.url.path, "type": type(exc).__name__, "msg": str(exc)}, "H0")
        # #endregion
        logger.exception("Unhandled exception in middleware")
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc) or "Internal server error",
                "type": type(exc).__name__,
            },
        )


@app.get("/")
def root() -> dict:
    """Root endpoint."""
    return {"message": f"Welcome to {settings.app_name} API", "docs": "/docs"}
