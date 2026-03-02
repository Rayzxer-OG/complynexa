"""Auth schemas."""

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)


class OnboardingOrganization(BaseModel):
    """Organization and unit fields for combined onboarding. Optional fields use defaults for units table (non-null columns)."""

    organization_name: str = Field(..., min_length=1, max_length=256)
    unit_name: str = Field(..., min_length=1, max_length=256)
    address: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1, max_length=128)
    industry_id: str = Field(..., min_length=1, max_length=128)
    business_type_id: str = Field("", max_length=128)
    employees: int = Field(0, ge=0)
    manufacturing: bool = False
    electrical_load: float = Field(0.0, ge=0)


class OnboardingUser(BaseModel):
    """Admin user fields for combined onboarding."""

    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    mobile: str = Field("", max_length=32)
    alternate_email: str | None = Field(None, max_length=255)
    alternate_mobile: str | None = Field(None, max_length=32)


class OnboardingBody(BaseModel):
    """Combined payload: organization/unit + admin user."""

    organization: OnboardingOrganization
    user: OnboardingUser


class UserLogin(BaseModel):
    """Schema for login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
