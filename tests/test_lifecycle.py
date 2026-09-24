"""
Integration tests for Donation Lifecycle, Capacity Snapshot, and Offer Flow (Phase 3).
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.sim.seed import run_seed


@pytest.fixture(scope="function", autouse=True)
async def seed_data():
    """Seed test data before running lifecycle tests."""
    await run_seed()


@pytest.mark.asyncio
async def test_donation_preview_and_create_flow():
    """Test preview -> create donation -> check matching & allocation -> list donations."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Login as donor
        login_resp = await client.post(
            "/api/v1/auth/demo",
            json={"role": "donor"},
        )
        assert login_resp.status_code == 200
        donor_token = login_resp.json()["access_token"]
        donor_headers = {"Authorization": f"Bearer {donor_token}"}

        now = datetime.now(UTC)
        donation_payload = {
            "items": [
                {"name": "Paneer Butter Masala", "portions": 30, "weight_kg": 12.0},
                {"name": "Jeera Rice", "portions": 30, "weight_kg": 9.0},
            ],
            "diet": "veg",
            "storage": "hot",
            "category": "cooked_meals",
            "prepared_at": now.isoformat(),
            "pickup_window": {
                "start": now.isoformat(),
                "end": (now + timedelta(hours=2)).isoformat(),
            },
            "pickup": {
                "lat": 28.6139,
                "lng": 77.2090,
                "address": "Connaught Place Donor Kitchen",
            },
        }

        # 2. Preview feasibility
        preview_resp = await client.post(
            "/api/v1/donations/preview",
            json=donation_payload,
            headers=donor_headers,
        )
        assert preview_resp.status_code == 200
        preview_data = preview_resp.json()
        assert preview_data["feasible_recipients"] > 0
        assert preview_data["best"] is not None
        assert "score" in preview_data["best"]

        # 3. Post surplus donation
        create_resp = await client.post(
            "/api/v1/donations",
            json=donation_payload,
            headers={"Authorization": f"Bearer {donor_token}", "Idempotency-Key": "post-don-1"},
        )
        assert create_resp.status_code == 201
        don_data = create_resp.json()
        assert don_data["status"] in ("matched", "partially_matched")
        assert len(don_data["allocations"]) > 0
        donation_id = don_data["id"]

        # Verify donor sees plain pickup_otp for allocations
        assert don_data["allocations"][0]["pickup_otp"] is not None

        # 4. List donations
        list_resp = await client.get("/api/v1/donations", headers=donor_headers)
        assert list_resp.status_code == 200
        items = list_resp.json()["items"]
        assert any(item["id"] == donation_id for item in items)


@pytest.mark.asyncio
async def test_recipient_capacity_and_offer_accept():
    """Test recipient views capacity snapshot -> sees pending offer -> accepts offer."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Login as demo recipient
        demo_resp = await client.post(
            "/api/v1/auth/demo",
            json={"role": "recipient"},
        )
        assert demo_resp.status_code == 200
        recip_token = demo_resp.json()["access_token"]
        recip_headers = {"Authorization": f"Bearer {recip_token}"}

        # 2. Check CapacitySnapshot
        cap_resp = await client.get("/api/v1/org/capacity", headers=recip_headers)
        assert cap_resp.status_code == 200
        cap_data = cap_resp.json()
        assert "max_portions" in cap_data
        assert "available_now" in cap_data
        assert "projection" in cap_data
        assert len(cap_data["projection"]) > 0

        # 3. Donor posts a donation
        donor_login = await client.post(
            "/api/v1/auth/demo",
            json={"role": "donor"},
        )
        assert donor_login.status_code == 200
        donor_token = donor_login.json()["access_token"]

        now = datetime.now(UTC)
        don_payload = {
            "items": [{"name": "Mixed Veg Pulao", "portions": 25}],
            "diet": "veg",
            "storage": "ambient",
            "category": "cooked_meals",
            "prepared_at": now.isoformat(),
            "pickup_window": {
                "start": now.isoformat(),
                "end": (now + timedelta(hours=2)).isoformat(),
            },
            "pickup": {"lat": 28.6139, "lng": 77.2090, "address": "Central Delhi"},
        }
        don_res = await client.post(
            "/api/v1/donations",
            json=don_payload,
            headers={"Authorization": f"Bearer {donor_token}", "Idempotency-Key": "recip-test-don"},
        )
        assert don_res.status_code == 201
        don_id = don_res.json()["id"]

        # 4. Check recipient pending offers
        offers_resp = await client.get(
            "/api/v1/offers?status=pending",
            headers=recip_headers,
        )
        assert offers_resp.status_code == 200
        offers = offers_resp.json()

        matching_offers = [o for o in offers if str(o["donation"]["id"]) == str(don_id)]
        if matching_offers:
            offer = matching_offers[0]
            offer_id = offer["id"]

            # 5. Accept offer
            accept_resp = await client.post(
                f"/api/v1/offers/{offer_id}/accept",
                json={"portions": offer["offered_portions"]},
                headers={**recip_headers, "Idempotency-Key": f"accept-{offer_id}"},
            )
            assert accept_resp.status_code == 200
            assert accept_resp.json()["status"] == "accepted"

            # 6. Accepting again fails with OFFER_NOT_PENDING
            re_accept_resp = await client.post(
                f"/api/v1/offers/{offer_id}/accept",
                json={},
                headers={**recip_headers, "Idempotency-Key": f"re-accept-{offer_id}"},
            )
            assert re_accept_resp.status_code == 400
            assert re_accept_resp.json()["error"]["code"] == "OFFER_NOT_PENDING"


@pytest.mark.asyncio
async def test_offer_decline_flow():
    """Test declining an offer marks it declined and releases held capacity."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        recip_login = await client.post("/api/v1/auth/demo", json={"role": "recipient"})
        recip_token = recip_login.json()["access_token"]
        recip_headers = {"Authorization": f"Bearer {recip_token}"}

        donor_login = await client.post("/api/v1/auth/demo", json={"role": "donor"})
        donor_token = donor_login.json()["access_token"]

        now = datetime.now(UTC)
        don_payload = {
            "items": [{"name": "Dal Makhani", "portions": 20}],
            "diet": "veg",
            "storage": "ambient",
            "category": "cooked_meals",
            "prepared_at": now.isoformat(),
            "pickup_window": {
                "start": now.isoformat(),
                "end": (now + timedelta(hours=2)).isoformat(),
            },
            "pickup": {"lat": 28.6139, "lng": 77.2090, "address": "Central Delhi"},
        }
        don_res = await client.post(
            "/api/v1/donations",
            json=don_payload,
            headers={"Authorization": f"Bearer {donor_token}", "Idempotency-Key": "decline-don-1"},
        )
        assert don_res.status_code == 201
        don_id = don_res.json()["id"]

        offers_resp = await client.get("/api/v1/offers?status=pending", headers=recip_headers)
        offers = offers_resp.json()
        matching_offers = [o for o in offers if str(o["donation"]["id"]) == str(don_id)]
        if matching_offers:
            offer_id = matching_offers[0]["id"]
            decline_resp = await client.post(
                f"/api/v1/offers/{offer_id}/decline",
                json={"reason": "Storage full temporarily"},
                headers=recip_headers,
            )
            assert decline_resp.status_code == 200
            assert decline_resp.json()["status"] == "declined"


@pytest.mark.asyncio
async def test_org_capacity_endpoints():
    """Test capacity adjust and mark-full endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        recip_login = await client.post("/api/v1/auth/demo", json={"role": "recipient"})
        recip_token = recip_login.json()["access_token"]
        recip_headers = {"Authorization": f"Bearer {recip_token}"}

        # 1. Adjust capacity
        adj_resp = await client.post(
            "/api/v1/org/capacity/adjust",
            json={"delta_portions": -10, "reason": "Refrigerator maintenance"},
            headers=recip_headers,
        )
        assert adj_resp.status_code == 200
        assert "available_now" in adj_resp.json()

        # 2. Mark org full
        full_resp = await client.post(
            "/api/v1/org/capacity/full",
            headers=recip_headers,
        )
        assert full_resp.status_code == 200
        assert full_resp.json()["available_now"] == 0


@pytest.mark.asyncio
async def test_donation_detail_and_cancel():
    """Test retrieving donation details and cancelling a donation."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        donor_login = await client.post("/api/v1/auth/demo", json={"role": "donor"})
        donor_token = donor_login.json()["access_token"]
        donor_headers = {"Authorization": f"Bearer {donor_token}"}

        now = datetime.now(UTC)
        don_payload = {
            "items": [{"name": "Idli Sambar", "portions": 15}],
            "diet": "veg",
            "storage": "ambient",
            "category": "cooked_meals",
            "prepared_at": now.isoformat(),
            "pickup_window": {
                "start": now.isoformat(),
                "end": (now + timedelta(hours=2)).isoformat(),
            },
            "pickup": {"lat": 28.6139, "lng": 77.2090, "address": "Delhi Donor"},
        }
        res = await client.post(
            "/api/v1/donations",
            json=don_payload,
            headers={"Authorization": f"Bearer {donor_token}", "Idempotency-Key": "cancel-don-1"},
        )
        don_id = res.json()["id"]

        # Detail
        detail_resp = await client.get(f"/api/v1/donations/{don_id}", headers=donor_headers)
        assert detail_resp.status_code == 200
        assert detail_resp.json()["id"] == don_id

        # Cancel
        cancel_resp = await client.post(f"/api/v1/donations/{don_id}/cancel", headers=donor_headers)
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelled"

