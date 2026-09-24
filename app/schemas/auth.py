import uuid
from typing import Any

from pydantic import EmailStr, Field

from app.core.config import Role
from app.schemas.common import SchemaBase


class RegisterRequest(SchemaBase):
    role: Role
    name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=10, max_length=32)
    email: EmailStr | None = None
    password: str = Field(..., min_length=6, max_length=128)
    profile: dict[str, Any] = Field(default_factory=dict)
    locale: str = Field(default="en", max_length=10)


class LoginRequest(SchemaBase):
    phone_or_email: str
    password: str


class TokenRefreshRequest(SchemaBase):
    refresh_token: str


class DemoLoginRequest(SchemaBase):
    role: Role


class TokenResponse(SchemaBase):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: uuid.UUID
    role: Role


class UserResponse(SchemaBase):
    id: uuid.UUID
    role: Role
    name: str
    phone: str
    phone_masked: str | None = None
    email: str | None = None
    is_active: bool
    locale: str
    profile: dict[str, Any] | None = None
