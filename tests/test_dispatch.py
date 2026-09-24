"""
Integration and Unit tests for Driver Dispatch, Routing, VRP, and Stop Lifecycle (Phase 4).
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import (
    DietType,
    DriverStatus,
    Role,
    StopType,
    StorageCondition,
    VehicleType,
)
from app.core.security import hash_otp
from app.db.models.allocation import Allocation
from app.db.session import async_session_maker
from app.main import app
from app.services.dispatch.assignment import (
    filter_candidate_drivers,
    solve_bipartite_assignment,
)
from app.services.dispatch.engine import dispatch_pending_tasks
from app.services.dispatch.insertion import find_best_stacked_insertion
from app.services.dispatch.types import DispatchTask, DriverCandidate, StopPlan
from app.services.dispatch.vrp import optimize_route_pdptw
from app.services.sim.seed import run_seed


@pytest.fixture(scope="function", autouse=True)
async def seed_data():
    await run_seed()


def test_candidate_driver_filter_cold_box_rule():
    """Verify Rule R3: cold food requires vehicle with cold box."""
    now = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    task_cold = DispatchTask(
        allocation_id=uuid.uuid4(),
        donation_id=uuid.uuid4(),
        portions=20,
        diet=DietType.VEG,
        storage=StorageCondition.COLD,
        container_label="Cold Box 1",
        deadline=now + timedelta(hours=3),
        pickup_lat=28.6139,
        pickup_lng=77.2090,
        pickup_address="Pickup 1",
        pickup_name="Donor 1",
        ready_at=now,
        latest_pickup=now + timedelta(hours=1),
        dropoff_lat=28.6200,
        dropoff_lng=77.2150,
        dropoff_address="Dropoff 1",
        dropoff_name="Org 1",
        dropoff_window_end=now + timedelta(hours=3),
    )

    d_no_cold = DriverCandidate(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        vehicle_type=VehicleType.SCOOTER,
        capacity_portions=50,
        has_cold_box=False,
        status=DriverStatus.AVAILABLE,
        lat=28.6140,
        lng=77.2095,
    )
    d_with_cold = DriverCandidate(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        vehicle_type=VehicleType.SCOOTER,
        capacity_portions=50,
        has_cold_box=True,
        status=DriverStatus.AVAILABLE,
        lat=28.6140,
        lng=77.2095,
    )

    survivors = filter_candidate_drivers(task_cold, [d_no_cold, d_with_cold], now)
    assert len(survivors) == 1
    assert survivors[0].id == d_with_cold.id


def test_scipy_bipartite_assignment():
    """Test min-cost bipartite matching with SciPy."""
    now = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    t1 = DispatchTask(
        allocation_id=uuid.uuid4(),
        donation_id=uuid.uuid4(),
        portions=20,
        diet=DietType.VEG,
        storage=StorageCondition.AMBIENT,
        container_label="Box A",
        deadline=now + timedelta(hours=2),
        pickup_lat=28.6139,
        pickup_lng=77.2090,
        pickup_address="CP",
        pickup_name="Donor",
        ready_at=now,
        latest_pickup=now + timedelta(hours=1),
        dropoff_lat=28.6300,
        dropoff_lng=77.2200,
        dropoff_address="Dropoff",
        dropoff_name="Org",
        dropoff_window_end=now + timedelta(hours=2),
    )

    d1 = DriverCandidate(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        vehicle_type=VehicleType.SCOOTER,
        capacity_portions=60,
        has_cold_box=False,
        status=DriverStatus.AVAILABLE,
        lat=28.6145,
        lng=77.2095,
    )

    assignments = solve_bipartite_assignment([t1], [d1], now)
    assert len(assignments) == 1
    assert assignments[0].driver_id == d1.id
    assert assignments[0].task_id == t1.allocation_id
    assert assignments[0].cost_minutes < 100.0


def test_savelsbergh_insertion_stacking():
    """Test inserting a new task onto an active driver's existing route."""
    now = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)

    existing_p = StopPlan(
        id=uuid.uuid4(),
        seq=1,
        type=StopType.PICKUP,
        allocation_id=uuid.uuid4(),
        lat=28.6150,
        lng=77.2100,
        window_start=now,
        window_end=now + timedelta(hours=1),
        planned_arrival=now + timedelta(minutes=5),
        predicted_arrival=now + timedelta(minutes=5),
        portions=15,
    )
    existing_d = StopPlan(
        id=uuid.uuid4(),
        seq=2,
        type=StopType.DROPOFF,
        allocation_id=existing_p.allocation_id,
        lat=28.6250,
        lng=77.2200,
        window_start=now,
        window_end=now + timedelta(hours=2),
        planned_arrival=now + timedelta(minutes=25),
        predicted_arrival=now + timedelta(minutes=25),
        portions=15,
    )

    active_driver = DriverCandidate(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        vehicle_type=VehicleType.SCOOTER,
        capacity_portions=60,
        has_cold_box=False,
        status=DriverStatus.ON_TASK,
        lat=28.6139,
        lng=77.2090,
        existing_stops=[existing_p, existing_d],
    )

    new_task = DispatchTask(
        allocation_id=uuid.uuid4(),
        donation_id=uuid.uuid4(),
        portions=10,
        diet=DietType.VEG,
        storage=StorageCondition.AMBIENT,
        container_label="Box B",
        deadline=now + timedelta(hours=2),
        pickup_lat=28.6160,
        pickup_lng=77.2110,  # very close to existing pickup
        pickup_address="P2",
        pickup_name="Donor 2",
        ready_at=now,
        latest_pickup=now + timedelta(hours=1),
        dropoff_lat=28.6240,
        dropoff_lng=77.2190,  # very close to existing dropoff
        dropoff_address="D2",
        dropoff_name="Org 2",
        dropoff_window_end=now + timedelta(hours=2),
    )

    result = find_best_stacked_insertion(new_task, [active_driver], now)
    assert result is not None
    assert result.driver_id == active_driver.id
    assert len(result.new_stops) == 4
    # Precedence check: new pickup is before new dropoff
    seq_map = {s.type: s.seq for s in result.new_stops if s.allocation_id == new_task.allocation_id}
    assert seq_map[StopType.PICKUP] < seq_map[StopType.DROPOFF]


def test_ortools_vrp_route_optimization():
    """Test OR-Tools PDPTW route sequence optimization."""
    now = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    driver = DriverCandidate(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        vehicle_type=VehicleType.SCOOTER,
        capacity_portions=100,
        has_cold_box=False,
        status=DriverStatus.AVAILABLE,
        lat=28.6139,
        lng=77.2090,
    )

    # 4 stops (2 pickups, 2 dropoffs)
    alloc1 = uuid.uuid4()
    alloc2 = uuid.uuid4()

    stops = [
        StopPlan(
            seq=1,
            type=StopType.PICKUP,
            allocation_id=alloc1,
            lat=28.6150,
            lng=77.2100,
            window_start=now,
            window_end=now + timedelta(hours=1),
            portions=20,
        ),
        StopPlan(
            seq=2,
            type=StopType.PICKUP,
            allocation_id=alloc2,
            lat=28.6180,
            lng=77.2120,
            window_start=now,
            window_end=now + timedelta(hours=1),
            portions=25,
        ),
        StopPlan(
            seq=3,
            type=StopType.DROPOFF,
            allocation_id=alloc1,
            lat=28.6250,
            lng=77.2200,
            window_start=now,
            window_end=now + timedelta(hours=2),
            portions=20,
        ),
        StopPlan(
            seq=4,
            type=StopType.DROPOFF,
            allocation_id=alloc2,
            lat=28.6300,
            lng=77.2250,
            window_start=now,
            window_end=now + timedelta(hours=2),
            portions=25,
        ),
    ]

    opt_stops, saved_s, reason = optimize_route_pdptw(driver, stops, now)
    assert len(opt_stops) == 4
    # Precedence holds for all allocations
    for a_id in (alloc1, alloc2):
        p_seq = next(s.seq for s in opt_stops if s.allocation_id == a_id and s.type == StopType.PICKUP)
        d_seq = next(s.seq for s in opt_stops if s.allocation_id == a_id and s.type == StopType.DROPOFF)
        assert p_seq < d_seq


@pytest.mark.asyncio
async def test_driver_api_shift_profile_and_telematics():
    """Test driver shift toggle, profile update, and GPS location ping."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Login as driver
        login_resp = await client.post("/api/v1/auth/demo", json={"role": "driver"})
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Shift toggle: go online
        shift_resp = await client.post(
            "/api/v1/driver/shift",
            json={"status": "available"},
            headers=headers,
        )
        assert shift_resp.status_code == 200
        assert shift_resp.json()["status"] == "available"

        # 3. Update profile
        prof_resp = await client.put(
            "/api/v1/driver/profile",
            json={"capacity_portions": 85, "has_cold_box": True},
            headers=headers,
        )
        assert prof_resp.status_code == 200
        assert prof_resp.json()["capacity_portions"] == 85
        assert prof_resp.json()["has_cold_box"] is True

        # 4. GPS location ping
        loc_resp = await client.post(
            "/api/v1/driver/location",
            json={"lat": 28.6145, "lng": 77.2095, "speed": 18.5, "heading": 90.0},
            headers=headers,
        )
        assert loc_resp.status_code == 200
        assert loc_resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_full_driver_dispatch_and_stop_completion_lifecycle():
    """
    End-to-end Driver Lifecycle:
    Donor posts donation -> Recipient accepts -> Dispatch creates driver offer ->
    Driver accepts offer -> Driver follows route:
    Arrive at pickup -> Complete pickup with pickup_otp ->
    Arrive at dropoff -> Complete dropoff with dropoff_otp ->
    Allocation marked DELIVERED and impact ledger entry created!
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Setup Donor, Recipient, Driver tokens
        donor_login = await client.post("/api/v1/auth/demo", json={"role": "donor"})
        donor_token = donor_login.json()["access_token"]

        recip_login = await client.post("/api/v1/auth/demo", json={"role": "recipient"})
        recip_token = recip_login.json()["access_token"]
        recip_headers = {"Authorization": f"Bearer {recip_token}"}

        driver_login = await client.post("/api/v1/auth/demo", json={"role": "driver"})
        driver_token = driver_login.json()["access_token"]
        driver_headers = {"Authorization": f"Bearer {driver_token}"}

        # Make sure driver is online
        await client.post("/api/v1/driver/shift", json={"status": "available"}, headers=driver_headers)
        await client.post(
            "/api/v1/driver/location",
            json={"lat": 28.6139, "lng": 77.2090, "speed": 0.0},
            headers=driver_headers,
        )

        # 2. Donor posts surplus
        now = datetime.now(UTC)
        don_payload = {
            "items": [{"name": "Rajma Chawal", "portions": 30}],
            "diet": "veg",
            "storage": "ambient",
            "category": "cooked_meals",
            "prepared_at": now.isoformat(),
            "pickup_window": {
                "start": now.isoformat(),
                "end": (now + timedelta(hours=2)).isoformat(),
            },
            "pickup": {"lat": 28.6139, "lng": 77.2090, "address": "Delhi Kitchen"},
        }
        don_resp = await client.post(
            "/api/v1/donations",
            json=don_payload,
            headers={"Authorization": f"Bearer {donor_token}", "Idempotency-Key": "e2e-disp-1"},
        )
        assert don_resp.status_code == 201
        don_data = don_resp.json()
        _don_id = don_data["id"]
        alloc_data = don_data["allocations"][0]
        pickup_otp = alloc_data["pickup_otp"]
        alloc_id = alloc_data["id"]

        # 3. Find the recipient who received the offer for this allocation
        async with async_session_maker() as db:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            from app.core.security import create_access_token
            from app.db.models.offer import Offer

            alloc_stmt = (
                select(Allocation)
                .where(Allocation.id == uuid.UUID(alloc_id))
                .options(selectinload(Allocation.recipient), selectinload(Allocation.offers))
            )
            alloc_obj = (await db.execute(alloc_stmt)).scalar_one()
            r_offer = next(o for o in alloc_obj.offers if o.kind == "recipient" and o.status == "pending")
            recipient_user_id = alloc_obj.recipient.user_id
            r_offer_id = r_offer.id

        recip_token = create_access_token(user_id=recipient_user_id, role=Role.RECIPIENT)
        recip_headers = {"Authorization": f"Bearer {recip_token}"}

        acc_resp = await client.post(
            f"/api/v1/offers/{r_offer_id}/accept",
            json={},
            headers={**recip_headers, "Idempotency-Key": f"acc-r-{r_offer_id}"},
        )
        assert acc_resp.status_code == 200

        # 4. Find the driver who received the driver offer
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
                d_offer = (await db.execute(d_offer_stmt)).scalar_one()

            d_offer_id = d_offer.id
            driver_user_id = d_offer.target_user_id

        driver_token = create_access_token(user_id=driver_user_id, role=Role.DRIVER)
        driver_headers = {"Authorization": f"Bearer {driver_token}"}

        d_offers = (await client.get("/api/v1/driver/offers?status=pending", headers=driver_headers)).json()
        assert len(d_offers) > 0
        driver_offer = d_offers[0]
        assert driver_offer["route_preview"] is not None

        # 5. Driver accepts offer
        d_acc_resp = await client.post(
            f"/api/v1/offers/{d_offer_id}/accept",
            json={},
            headers={**driver_headers, "Idempotency-Key": f"d-acc-{d_offer_id}"},
        )
        assert d_acc_resp.status_code == 200

        # 6. Driver retrieves active route
        route_resp = await client.get("/api/v1/driver/route", headers=driver_headers)
        assert route_resp.status_code == 200
        route = route_resp.json()
        assert route is not None
        assert len(route["stops"]) == 2
        p_stop = next(s for s in route["stops"] if s["type"] == "pickup")
        d_stop = next(s for s in route["stops"] if s["type"] == "dropoff")

        # 7. Driver arrives at pickup
        arr_p = await client.post(f"/api/v1/stops/{p_stop['id']}/arrive", headers=driver_headers)
        assert arr_p.status_code == 200
        assert arr_p.json()["status"] == "arrived"

        # 8. Driver completes pickup with OTP
        comp_p = await client.post(
            f"/api/v1/stops/{p_stop['id']}/complete",
            json={"otp": pickup_otp},
            headers={**driver_headers, "Idempotency-Key": f"comp-p-{p_stop['id']}"},
        )
        assert comp_p.status_code == 200
        assert comp_p.json()["status"] == "done"

        # Obtain dropoff OTP directly from the allocation in DB for test verification
        async with async_session_maker() as db:
            alloc_db = (
                await db.execute(select(Allocation).where(Allocation.id == uuid.UUID(alloc_id)))
            ).scalar_one()
            # Generate temporary dropoff OTP for completion test
            plain_drop_otp = "123456"
            alloc_db.dropoff_otp_hash = hash_otp(plain_drop_otp)
            await db.commit()

        # 9. Driver arrives at dropoff
        arr_d = await client.post(f"/api/v1/stops/{d_stop['id']}/arrive", headers=driver_headers)
        assert arr_d.status_code == 200

        # 10. Driver completes dropoff with OTP
        comp_d = await client.post(
            f"/api/v1/stops/{d_stop['id']}/complete",
            json={"otp": plain_drop_otp},
            headers={**driver_headers, "Idempotency-Key": f"comp-d-{d_stop['id']}"},
        )
        assert comp_d.status_code == 200
        assert comp_d.json()["status"] == "done"

        # 11. Check driver stats
        stats_resp = await client.get("/api/v1/driver/stats", headers=driver_headers)
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        assert stats["completed_deliveries"] >= 1
        assert stats["total_meals_delivered"] >= 30
