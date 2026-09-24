import json
from typing import Any

from fastapi import Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ValidationException


class Idempotent:
    """FastAPI dependency to extract optional or required Idempotency-Key header."""

    def __init__(self, required: bool = False):
        self.required = required

    async def __call__(
        self,
        idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    ) -> str | None:
        if self.required and not idempotency_key:
            raise ValidationException("Idempotency-Key header is required for this request.")
        return idempotency_key


async def get_idempotent_response(
    db: AsyncSession,
    key: str,
    user_id: str,
    endpoint: str,
) -> dict[str, Any] | None:
    """Retrieve previously recorded response for an idempotency key."""
    # We dynamically import the model to avoid circular imports
    from app.db.models.idempotency import IdempotencyRecord

    stmt = select(IdempotencyRecord).where(
        IdempotencyRecord.key == key,
        IdempotencyRecord.user_id == user_id,
        IdempotencyRecord.endpoint == endpoint,
    )
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()
    if record and record.response:
        if isinstance(record.response, str):
            return json.loads(record.response)
        return record.response
    return None


async def save_idempotent_response(
    db: AsyncSession,
    key: str,
    user_id: str,
    endpoint: str,
    response_data: dict[str, Any],
) -> None:
    """Store idempotent response for subsequent identical requests."""
    from app.db.models.idempotency import IdempotencyRecord

    record = IdempotencyRecord(
        key=key,
        user_id=user_id,
        endpoint=endpoint,
        response=response_data,
    )
    db.add(record)
    await db.flush()
