"""API v1 routes."""

from fastapi import APIRouter

from app.api.v1 import auth, business_types, certificates, compliance, documents, health, industries, organization, upload_and_processing, units, users

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
# Explicit route so conditional-questions is always reachable (avoids sub-router 404 on some setups)
api_router.add_api_route(
    "/industries/conditional-questions",
    industries.get_industry_conditional_questions_query,
    methods=["GET"],
    tags=["industries"],
    summary="Industry conditional questions (query param)",
)
api_router.include_router(industries.router, prefix="/industries", tags=["industries"])
api_router.include_router(business_types.router, prefix="/business-types", tags=["business-types"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(organization.router, prefix="/organization", tags=["organization"])
api_router.include_router(units.router, prefix="/units", tags=["units"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["certificates"])
api_router.include_router(upload_and_processing.router, tags=["upload", "processing"])
