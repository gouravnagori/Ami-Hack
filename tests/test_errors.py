import pytest
from httpx import AsyncClient

from app.core.errors import format_error_response


def test_format_error_response():
    resp = format_error_response(
        code="CAPACITY_EXCEEDED",
        message="Asha Shelter can take 40 more portions right now.",
        details={"available": 40},
        request_id="req-abc-123",
    )
    assert resp["error"]["code"] == "CAPACITY_EXCEEDED"
    assert resp["error"]["message"] == "Asha Shelter can take 40 more portions right now."
    assert resp["error"]["details"]["available"] == 40
    assert resp["error"]["request_id"] == "req-abc-123"


@pytest.mark.asyncio
async def test_validation_error_format(client: AsyncClient):
    # Send invalid body to register
    resp = await client.post("/api/v1/auth/register", json={"role": "invalid_role"})
    assert resp.status_code == 422
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in data["error"]
