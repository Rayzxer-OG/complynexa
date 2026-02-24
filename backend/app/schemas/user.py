"""User schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Shared user fields."""

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user."""

    pass


class UserUpdate(BaseModel):
    """Schema for updating a user (all fields optional)."""

    email: EmailStr | None = None
    full_name: str | None = Field(None, min_length=1, max_length=255)
    is_active: bool | None = None


class UserResponse(UserBase):
    """Schema for user in API responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
