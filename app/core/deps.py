import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.clock import Clock, default_clock
from app.core.config import Role
from app.core.errors import ForbiddenException, UnauthenticatedException
from app.core.security import decode_token
from app.db.models.user import User
from app.db.session import get_db

CurrentUser = User
security = HTTPBearer(auto_error=False)


def get_clock() -> Clock:
    return default_clock


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not credentials:
        raise UnauthenticatedException("Authentication credentials were not provided.")

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except Exception:
        raise UnauthenticatedException("Invalid or expired authentication token.") from None

    if payload.get("type") != "access":
        raise UnauthenticatedException("Invalid token type: access token expected.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthenticatedException("Malformed token: missing subject.")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthenticatedException("Invalid user ID in token.") from None

    stmt = (
        select(User)
        .where(User.id == user_uuid)
        .options(
            selectinload(User.donor_profile),
            selectinload(User.recipient_profile),
            selectinload(User.driver_profile),
        )
    )
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise UnauthenticatedException("User associated with this token no longer exists.")

    if not user.is_active:
        raise ForbiddenException("User account is inactive.")

    return user


def require_role(*roles: Role) -> Callable[[User], User]:
    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles and current_user.role != Role.ADMIN:
            raise ForbiddenException(
                f"Role '{current_user.role}' is not authorized to access this resource. Required: {[str(r) for r in roles]}"
            )
        return current_user

    return role_checker
