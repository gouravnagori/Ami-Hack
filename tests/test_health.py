import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthz(client: AsyncClient):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "goldenhour-api"


@pytest.mark.asyncio
async def test_readyz(client: AsyncClient):
    resp = await client.get("/readyz")
    assert resp.status_code in [200, 503]
    data = resp.json()
    assert "status" in data
    assert "dependencies" in data


@pytest.mark.asyncio
async def test_server_time(client: AsyncClient):
    resp = await client.get("/time")
    assert resp.status_code == 200
    data = resp.json()
    assert "server_time" in data
    assert "timestamp" in data
    assert data["timezone"] == "UTC"


@pytest.mark.asyncio
async def test_request_id_header(client: AsyncClient):
    custom_id = "test-req-id-12345"
    resp = await client.get("/healthz", headers={"X-Request-ID": custom_id})
    assert resp.headers.get("X-Request-ID") == custom_id
