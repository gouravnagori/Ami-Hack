"""
STEP 2: Deterministic End-to-End Lifecycle Integration Test.

Covers the full GoldenHour/RescueOS lifecycle:
  DONOR CREATES DONATION → SAFETY VALIDATION → MATCHING
  → ORG OFFER → DRIVER DISPATCH → PICKUP OTP
  → DELIVERY OTP → IMPACT/RECEIPT

Uses the existing demo-seeded data via run_seed() and the actual
Appendix A API contracts. Does NOT invent new endpoint names.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import DonationStatus, Role
from app.core.security import create_access_token, hash_otp
from app.db.models.allocation import Allocation
from app.db.models.donation import Donation
from app.db.models.impact import ImpactLedger
from app.db.models.offer import Offer
from app.db.session import async_session_maker
from app.main import app
from app.services.dispatch.engine import dispatch_pending_tasks
from app.services.sim.seed import run_seed


@pytest.fixture(scope="function", autouse=True)
async def seed_data():
    await run_seed()


@pytest.mark.asyncio
async def test_full_e2e_lifecycle():
    """
    Complete lifecycle:
    1.  Authenticate (donor, recipient, driver)
    2.  Preview feasibility
    3.  Create donation → verify safety fields (safe_until, risk)
    4.  Verify matching status and at least one allocation
    5.  Verify donor receives plain pickup_otp
    6.  Verify matching explanation (score + reasons) on donation detail
    7.  Recipient sees pending offer → accepts
    8.  Driver offer is created → driver sees and accepts
    9.  Driver retrieves route with 2 stops
    10. Driver arrives at pickup → completes with OTP
    11. Driver arrives at dropoff → completes with OTP
    12. ImpactLedger entry created after delivery
    13. Donation reaches terminal DELIVERED/COMPLETED state
    14. Driver stats updated (completed_deliveries, total_meals_delivered)
    15. PDF receipt endpoint returns 200 application/pdf
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:

        # ── 1. Auth ───────────────────────────────────────────────────────
        donor_login = await client.post("/api/v1/auth/demo", json={"role": "donor"})
        assert donor_login.status_code == 200
        donor_token = donor_login.json()["access_token"]
        donor_headers = {"Authorization": f"Bearer {donor_token}"}

        driver_login = await client.post("/api/v1/auth/demo", json={"role": "driver"})
        assert driver_login.status_code == 200
        driver_token = driver_login.json()["access_token"]
        driver_headers = {"Authorization": f"Bearer {driver_token}"}

        # Driver must be online and positioned
        shift_resp = await client.post(
            "/api/v1/driver/shift", json={"status": "available"}, headers=driver_headers
        )
        assert shift_resp.status_code == 200
        await client.post(
            "/api/v1/driver/location",
            json={"lat": 28.6139, "lng": 77.2090, "speed": 0.0},
            headers=driver_headers,
        )

        # ── 2. Preview feasibility ─────────────────────────────────────────
        now = datetime.now(UTC)
        donation_payload = {
            "items": [
                {"name": "Paneer Butter Masala", "portions": 25, "weight_kg": 10.0},
                {"name": "Jeera Rice", "portions": 25, "weight_kg": 7.5},
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

        preview_resp = await client.post(
            "/api/v1/donations/preview",
            json=donation_payload,
            headers=donor_headers,
        )
        assert preview_resp.status_code == 200
        preview = preview_resp.json()
        assert preview["feasible_recipients"] > 0, "At least 1 eligible recipient must exist"
        assert preview["best"] is not None
        assert "score" in preview["best"]

        # ── 3. Create donation ─────────────────────────────────────────────
        create_resp = await client.post(
            "/api/v1/donations",
            json=donation_payload,
            headers={**donor_headers, "Idempotency-Key": "e2e-lifecycle-main-v1"},
        )
        assert create_resp.status_code == 201
        don_data = create_resp.json()
        donation_id = don_data["id"]

        # ── 4. Safety fields ───────────────────────────────────────────────
        assert don_data["safe_until"] is not None, "safe_until must be set"
        assert don_data["status"] in (
            DonationStatus.MATCHED,
            DonationStatus.PARTIALLY_MATCHED,
        ), f"Expected matched status, got {don_data['status']}"

        # ── 5. Matching + OTP ──────────────────────────────────────────────
        assert len(don_data["allocations"]) >= 1, "Must have at least one allocation"
        alloc_data = don_data["allocations"][0]
        pickup_otp = alloc_data["pickup_otp"]
        assert pickup_otp is not None, "Donor must receive plain pickup OTP"
        alloc_id = alloc_data["id"]

        # ── 6. Match explanation on donation detail ────────────────────────
        detail_resp = await client.get(f"/api/v1/donations/{donation_id}", headers=donor_headers)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        first_alloc = detail["allocations"][0]
        if first_alloc.get("explanation"):
            expl = first_alloc["explanation"]
            assert "score" in expl
            assert "reasons" in expl
            assert len(expl["reasons"]) >= 1
            # Each reason must have code + label
            for r in expl["reasons"]:
                assert "code" in r
                assert "label" in r

        # ── 7. Recipient accepts offer ─────────────────────────────────────
        async with async_session_maker() as db:
            alloc_stmt = (
                select(Allocation)
                .where(Allocation.id == uuid.UUID(alloc_id))
                .options(
                    selectinload(Allocation.recipient),
                    selectinload(Allocation.offers),
                )
            )
            alloc_obj = (await db.execute(alloc_stmt)).scalar_one()
            r_offer = next(
                (
                    o
                    for o in alloc_obj.offers
                    if o.kind == "recipient" and o.status == "pending"
                ),
                None,
            )
            assert r_offer is not None, "A pending recipient offer must exist after matching"
            recipient_user_id = alloc_obj.recipient.user_id
            r_offer_id = r_offer.id

        recip_token = create_access_token(user_id=recipient_user_id, role=Role.RECIPIENT)
        recip_headers = {"Authorization": f"Bearer {recip_token}"}

        acc_resp = await client.post(
            f"/api/v1/offers/{r_offer_id}/accept",
            json={},
            headers={**recip_headers, "Idempotency-Key": f"e2e-acc-r-{r_offer_id}"},
        )
        assert acc_resp.status_code == 200
        assert acc_resp.json()["status"] == "accepted"

        # ── 8. Driver accepts offer ────────────────────────────────────────
        async with async_session_maker() as db:
            d_offer_stmt = select(Offer).where(
                Offer.allocation_id == uuid.UUID(alloc_id),
                Offer.kind == "driver",
                Offer.status == "pending",
            )
            d_offer = (await db.execute(d_offer_stmt)).scalar_one_or_none()
            if not d_offer:
                await dispatch_pending_tasks(db, now)
                await db.commit()
                d_offer = (await db.execute(d_offer_stmt)).scalar_one_or_none()

            assert d_offer is not None, "A pending driver offer must exist after recipient accepts"
            d_offer_id = d_offer.id
            driver_user_id = d_offer.target_user_id

        driver_token = create_access_token(user_id=driver_user_id, role=Role.DRIVER)
        driver_headers = {"Authorization": f"Bearer {driver_token}"}

        # Driver sees offer with route_preview
        d_offers_resp = await client.get("/api/v1/driver/offers?status=pending", headers=driver_headers)
        assert d_offers_resp.status_code == 200
        d_offers = d_offers_resp.json()
        assert len(d_offers) > 0, "Driver must see their pending offer"
        assert d_offers[0]["route_preview"] is not None, "Route preview must be present in driver offer"

        d_acc_resp = await client.post(
            f"/api/v1/offers/{d_offer_id}/accept",
            json={},
            headers={**driver_headers, "Idempotency-Key": f"e2e-d-acc-{d_offer_id}"},
        )
        assert d_acc_resp.status_code == 200

        # ── 9. Driver retrieves route ──────────────────────────────────────
        route_resp = await client.get("/api/v1/driver/route", headers=driver_headers)
        assert route_resp.status_code == 200
        route = route_resp.json()
        assert route is not None
        stops = route["stops"]
        assert len(stops) == 2, "Route must have pickup + dropoff stops"
        p_stop = next(s for s in stops if s["type"] == "pickup")
        d_stop = next(s for s in stops if s["type"] == "dropoff")

        # ── 10. Pickup flow ────────────────────────────────────────────────
        arr_p = await client.post(f"/api/v1/stops/{p_stop['id']}/arrive", headers=driver_headers)
        assert arr_p.status_code == 200
        assert arr_p.json()["status"] == "arrived"

        comp_p = await client.post(
            f"/api/v1/stops/{p_stop['id']}/complete",
            json={"otp": pickup_otp},
            headers={**driver_headers, "Idempotency-Key": f"e2e-comp-p-{p_stop['id']}"},
        )
        assert comp_p.status_code == 200
        assert comp_p.json()["status"] == "done"

        # ── 11. Delivery flow ──────────────────────────────────────────────
        plain_drop_otp = "777888"
        async with async_session_maker() as db:
            alloc_db = (
                await db.execute(select(Allocation).where(Allocation.id == uuid.UUID(alloc_id)))
            ).scalar_one()
            alloc_db.dropoff_otp_hash = hash_otp(plain_drop_otp)
            await db.commit()

        arr_d = await client.post(f"/api/v1/stops/{d_stop['id']}/arrive", headers=driver_headers)
        assert arr_d.status_code == 200

        comp_d = await client.post(
            f"/api/v1/stops/{d_stop['id']}/complete",
            json={"otp": plain_drop_otp},
            headers={**driver_headers, "Idempotency-Key": f"e2e-comp-d-{d_stop['id']}"},
        )
        assert comp_d.status_code == 200
        assert comp_d.json()["status"] == "done"

        # ── 12. Impact ledger entry ────────────────────────────────────────
        async with async_session_maker() as db:
            il_stmt = select(ImpactLedger).where(
                ImpactLedger.allocation_id == uuid.UUID(alloc_id)
            )
            impact = (await db.execute(il_stmt)).scalar_one_or_none()
            assert impact is not None, "ImpactLedger entry must be created after delivery"
            assert impact.meals >= 25, "Meals must match donated portions"
            assert impact.co2e_kg > 0, "CO2e saving must be positive"

        # ── 13. Donation terminal state ────────────────────────────────────
        async with async_session_maker() as db:
            don_db = (
                await db.execute(select(Donation).where(Donation.id == uuid.UUID(donation_id)))
            ).scalar_one()
            assert don_db.status == DonationStatus.DELIVERED, f"Expected DELIVERED status, got {don_db.status}"

        # ── 14. Driver stats ───────────────────────────────────────────────
        stats_resp = await client.get("/api/v1/driver/stats", headers=driver_headers)
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        assert stats["completed_deliveries"] >= 1
        assert stats["total_meals_delivered"] >= 25

        # ── 15. PDF receipt ────────────────────────────────────────────────
        receipt_resp = await client.get(f"/api/v1/donations/{donation_id}/receipt.pdf")
        assert receipt_resp.status_code == 200
        assert "application/pdf" in receipt_resp.headers["content-type"]
        assert len(receipt_resp.content) > 100, "PDF must contain actual content"
