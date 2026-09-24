import pytest
from httpx import AsyncClient

from app.core.security import hash_password, verify_password


def test_password_hashing():
    pw = "SuperSecretSecurePass123!"
    h = hash_password(pw)
    assert h.startswith("$argon2id$")
    assert verify_password(pw, h) is True
    assert verify_password("WrongPassword!", h) is False


@pytest.mark.asyncio
async def test_register_and_login_donor(client: AsyncClient):
    # Register donor
    reg_payload = {
        "role": "donor",
        "name": "Bhojan Caterers",
        "phone": "+919876543210",
        "email": "bhojan@example.com",
        "password": "SecurePassword123!",
        "profile": {
            "org_name": "Bhojan Caterers Pvt Ltd",
            "kind": "caterer",
            "address": "South Extension, New Delhi",
            "lat": 28.5678,
            "lng": 77.2145,
            "fssai_no": "FSSAI-9876543210",
        },
    }
    reg_resp = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    tokens = reg_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["role"] == "donor"

    # Login with phone
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"phone_or_email": "+919876543210", "password": "SecurePassword123!"},
    )
    assert login_resp.status_code == 200
    login_tokens = login_resp.json()
    assert "access_token" in login_tokens

    # Access /me
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_tokens['access_token']}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["name"] == "Bhojan Caterers"
    assert me_data["role"] == "donor"
    assert "phone_masked" in me_data
    assert "•••••" in me_data["phone_masked"]


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"phone_or_email": "+919876543210", "password": "IncorrectPassword!"},
    )
    assert login_resp.status_code == 401
    err = login_resp.json()
    assert err["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.asyncio
async def test_demo_login_all_roles(client: AsyncClient):
    for role in ["donor", "recipient", "driver", "admin"]:
        resp = await client.post("/api/v1/auth/demo", json={"role": role})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["role"] == role

        # Check /me for each demo role
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        assert me_resp.status_code == 200
        me = me_resp.json()
        assert me["role"] == role
