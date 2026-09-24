import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.idempotency import get_idempotent_response, save_idempotent_response


@pytest.mark.asyncio
async def test_idempotency_storage(db_session: AsyncSession):
    key = "idem-key-999"
    user_id = "user-123"
    endpoint = "/api/v1/offers/123/accept"
    payload = {"status": "accepted", "portions": 50}

    # Verify initially none
    resp = await get_idempotent_response(db_session, key, user_id, endpoint)
    assert resp is None

    # Save
    await save_idempotent_response(db_session, key, user_id, endpoint, payload)

    # Retrieve
    cached = await get_idempotent_response(db_session, key, user_id, endpoint)
    assert cached is not None
    assert cached["status"] == "accepted"
    assert cached["portions"] == 50
