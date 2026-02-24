"""API v1 routes."""

from fastapi import APIRouter

from app.api.v1 import auth, certificates, documents, health, upload_and_processing, users

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["certificates"])
api_router.include_router(upload_and_processing.router, tags=["upload", "processing"])
