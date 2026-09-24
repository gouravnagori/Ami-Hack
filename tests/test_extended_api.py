"""
Integration tests for extended API endpoints:
- Impact endpoints (public, donor, org)
- Donor parse, repeat, and PDF receipt download
- Recipient incoming allocations and delivery confirmation
- Admin live snapshot, simulation, chaos controls, and metrics
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app
from app.services.sim.seed import run_seed


@pytest.fixture(scope="function", autouse=True)
async def seed_data():
    from app.core.config import settings
    settings.CHAOS_TRAFFIC_SPIKE = False
    settings.CHAOS_OSRM_DOWN = False
    settings.CHAOS_DRIVER_DROP = False
    settings.CHAOS_ORG_FULL = False
    await run_seed()



@pytest.mark.asyncio
async def test_parse_and_repeat_and_receipt():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Login as donor
        login_resp = await client.post("/api/v1/auth/demo", json={"role": "donor"})
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Test /donations/parse
        parse_resp = await client.post(
            "/api/v1/donations/parse",
            json={"text": "We have 40 portions of piping hot veg pulao and dal"},
            headers=headers,
        )
        assert parse_resp.status_code == 200
        data = parse_resp.json()
        assert data["confidence"] > 0.0
        assert data["draft"] is not None
        assert data["draft"]["diet"] == "veg"
        assert data["draft"]["storage"] == "hot"

        # 3. Create a donation
        now = datetime.now(UTC)
        payload = {
            "items": [{"name": "Veg Pulao", "portions": 20, "weight_kg": 8.0}],
            "diet": "veg",
            "storage": "ambient",
            "category": "cooked_meals",
            "prepared_at": now.isoformat(),
            "pickup_window": {
                "start": now.isoformat(),
                "end": (now + timedelta(hours=3)).isoformat(),
            },
            "pickup": {"lat": 28.6139, "lng": 77.2090, "address": "Donor Kitchen"},
        }
        create_resp = await client.post("/api/v1/donations", json=payload, headers=headers)
        assert create_resp.status_code == 201
        don_id = create_resp.json()["id"]

        # 4. Download PDF receipt
        receipt_resp = await client.get(f"/api/v1/donations/{don_id}/receipt.pdf", headers=headers)
        assert receipt_resp.status_code == 200
        assert receipt_resp.headers["content-type"] == "application/pdf"
        assert receipt_resp.content.startswith(b"%PDF")

        # 5. Repeat donation
        repeat_resp = await client.post(f"/api/v1/donations/repeat/{don_id}", headers=headers)
        assert repeat_resp.status_code == 201
        new_don = repeat_resp.json()
        assert new_don["id"] != don_id
        assert new_don["total_portions"] == 20


@pytest.mark.asyncio
async def test_impact_endpoints():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Public impact (no auth needed)
        pub_resp = await client.get("/api/v1/impact/public")
        assert pub_resp.status_code == 200
        pub_data = pub_resp.json()
        assert "meals_rescued" in pub_data
        assert "weight_kg" in pub_data
        assert "co2e_kg_avoided" in pub_data

        # Donor impact
        donor_auth = await client.post("/api/v1/auth/demo", json={"role": "donor"})
        d_token = donor_auth.json()["access_token"]
        d_resp = await client.get("/api/v1/donor/impact", headers={"Authorization": f"Bearer {d_token}"})
        assert d_resp.status_code == 200
        assert "meals_rescued" in d_resp.json()

        # Recipient impact
        recip_auth = await client.post("/api/v1/auth/demo", json={"role": "recipient"})
        r_token = recip_auth.json()["access_token"]
        r_resp = await client.get("/api/v1/org/impact", headers={"Authorization": f"Bearer {r_token}"})
        assert r_resp.status_code == 200
        assert "meals_rescued" in r_resp.json()


@pytest.mark.asyncio
async def test_admin_endpoints():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        admin_auth = await client.post("/api/v1/auth/demo", json={"role": "admin"})
        assert admin_auth.status_code == 200
        a_token = admin_auth.json()["access_token"]
        headers = {"Authorization": f"Bearer {a_token}"}

        # 1. /admin/live
        live_resp = await client.get("/api/v1/admin/live", headers=headers)
        assert live_resp.status_code == 200
        live_data = live_resp.json()
        assert "donors" in live_data
        assert "orgs" in live_data
        assert "drivers" in live_data

        # 2. /admin/simulate/donation
        sim_resp = await client.post(
            "/api/v1/admin/simulate/donation",
            json={"count": 1, "scenario": "normal"},
            headers=headers,
        )
        assert sim_resp.status_code == 200
        assert sim_resp.json()["scenario"] == "normal"
        assert len(sim_resp.json()["created"]) == 1
        assert len(sim_resp.json()["donations"]) == 1

        # 3. /admin/chaos
        chaos_resp = await client.post(
            "/api/v1/admin/chaos",
            json={"kind": "traffic_spike"},
            headers=headers,
        )
        assert chaos_resp.status_code == 200
        assert "status" in chaos_resp.json()

        # 4. /admin/metrics
        metrics_resp = await client.get("/api/v1/admin/metrics", headers=headers)
        assert metrics_resp.status_code == 200
        m = metrics_resp.json()
        assert "active_donations" in m
        assert "deliveries_24h" in m
        assert "meals_rescued_24h" in m
        assert "online_drivers" in m

        # Reset chaos flags
        settings.CHAOS_TRAFFIC_SPIKE = False
        settings.CHAOS_OSRM_DOWN = False
        settings.CHAOS_DRIVER_DROP = False
        settings.CHAOS_ORG_FULL = False



@pytest.mark.asyncio
async def test_incoming_allocations_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        recip_auth = await client.post("/api/v1/auth/demo", json={"role": "recipient"})
        r_token = recip_auth.json()["access_token"]
        r_headers = {"Authorization": f"Bearer {r_token}"}

        incoming_resp = await client.get("/api/v1/org/incoming", headers=r_headers)
        assert incoming_resp.status_code == 200
        assert isinstance(incoming_resp.json(), list)
