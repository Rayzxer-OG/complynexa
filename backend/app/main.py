"""Compliance Tracker - FastAPI application entry point."""
import asyncio
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
from app.api.v1.compliance import save_compliance_attributes
from app.api.v1.industries import get_industry_conditional_questions_query
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.email_service import send_email_reminder
from app.services.reminder_service import (
    check_and_send_certificate_reminders,
    get_documents_requiring_reminder,
)
from app.services.scheduler_service import start as start_compliance_scheduler
from app.services.scheduler_service import shutdown as shutdown_compliance_scheduler

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


def run_reminder_job() -> None:
    """Run certificate expiry reminders (Resend). Uses its own DB session."""
    db = SessionLocal()
    try:
        check_and_send_certificate_reminders(db)
    finally:
        db.close()


def _lifespan_exception_handler(loop: asyncio.AbstractEventLoop, context: dict) -> None:
    """Suppress noisy CancelledError tracebacks during uvicorn --reload shutdown."""
    exc = context.get("exception")
    if isinstance(exc, asyncio.CancelledError):
        return  # Don't log; normal during reload or Ctrl+C
    loop.default_exception_handler(context)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    try:
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(_lifespan_exception_handler)
    except RuntimeError:
        pass
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

    # Verify database connection at startup
    db = SessionLocal()
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        logger.info("Database connected successfully (%s)", settings.database_url.split("@")[-1].split("/")[0])
    except Exception as e:
        logger.error(
            "Database connection failed: %s. Check: 1) PostgreSQL is running, 2) DATABASE_URL in .env (e.g. postgresql://user:password@localhost:5432/compliance_tracker), 3) Database exists (run: createdb compliance_tracker)",
            e,
        )
        raise
    finally:
        db.close()

    def run_reminder_scheduler_job() -> None:
        """Single daily job: log, then run document reminders and certificate reminders."""
        logger.info("Reminder scheduler job started")
        run_daily_reminder_check()
        run_reminder_job()

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_reminder_scheduler_job,
        CronTrigger(hour=9, minute=0),
        id="reminder_daily",
    )
    scheduler.start()
    logger.info("Reminder scheduler started (daily at 09:00 server time)")

    start_compliance_scheduler()

    try:
        yield
    except asyncio.CancelledError:
        # Normal during uvicorn --reload or Ctrl+C; avoid noisy traceback
        pass
    finally:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
        shutdown_compliance_scheduler()


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

# Register compliance-attributes first so bulk payload (unit_id + attributes) is always used (before api_router)
app.add_api_route(
    f"{settings.api_v1_prefix}/compliance/compliance-attributes",
    save_compliance_attributes,
    methods=["POST"],
    tags=["compliance"],
    summary="Save compliance attributes (bulk: unit_id + attributes list)",
)
# Register conditional-questions on the app so it is always reachable (before api_router)
app.add_api_route(
    f"{settings.api_v1_prefix}/industries/conditional-questions",
    get_industry_conditional_questions_query,
    methods=["GET"],
    tags=["industries"],
    summary="Industry conditional questions (query param)",
)
# With trailing slash (some clients send this)
app.add_api_route(
    f"{settings.api_v1_prefix}/industries/conditional-questions/",
    get_industry_conditional_questions_query,
    methods=["GET"],
    tags=["industries"],
    summary="Industry conditional questions (trailing slash)",
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
