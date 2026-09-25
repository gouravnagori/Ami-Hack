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
    city: str = Field(default="Jaipur", max_length=100)
    avatar_url: str | None = None
    otp: str | None = None


class SendOtpRequest(SchemaBase):
    email: EmailStr
    purpose: str = "login"  # "login" | "register"
    name: str | None = None


class LoginOtpRequest(SchemaBase):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=10)


class ProfileUpdateRequest(SchemaBase):
    name: str | None = None
    email: EmailStr | None = None
    city: str | None = None
    avatar_url: str | None = None
    profile: dict[str, Any] | None = None


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
    city: str | None = None
    avatar_url: str | None = None
    profile: dict[str, Any] | None = None
