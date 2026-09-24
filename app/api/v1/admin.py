"""
Admin/ops API — api/v1/admin.py

Endpoints:
  GET  /admin/live                         — live snapshot for ops map
  POST /admin/simulate/donation            — fire test donations
  POST /admin/chaos                        — failure injection
  GET  /admin/metrics                      — dispatch KPIs
"""

import random
import uuid
from datetime import UTC, datetime, timedelta

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import (
    AllocationStatus,
    DietType,
    DonationStatus,
    DriverStatus,
    Role,
    StorageCondition,
    settings,
)
from app.core.deps import require_role
from app.db.models.allocation import Allocation
from app.db.models.donation import Donation
from app.db.models.driver import Driver
from app.db.models.impact import ImpactLedger
from app.db.models.recipient import RecipientOrg
from app.db.models.route import Route
from app.db.session import async_session_maker, get_db
from app.services.dispatch.engine import dispatch_pending_tasks
from app.services.sim.seed import random_offset_coords

router = APIRouter(prefix="/admin", tags=["admin"])
logger = structlog.get_logger("goldenhour.admin")


# ---- Pydantic schemas ----

class SimulateDonationRequest(BaseModel):
    count: int = 1
    scenario: str = "normal"  # normal | wedding_night | rush_hour


class ChaosRequest(BaseModel):
    kind: str  # driver_drop | org_full | traffic_spike | osrm_down
    target_id: str | None = None


# ---- Live snapshot ----

@router.get("/live", summary="Live ops snapshot")
async def admin_live(
    _=Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Return live counts and status for the ops map."""
    now_utc = datetime.now(UTC)

    drivers_stmt = select(Driver)
    drivers = (await db.execute(drivers_stmt)).scalars().all()
    driver_rows = [
        {
            "id": str(d.id),
            "status": d.status,
            "vehicle": d.vehicle_type,
            "lat": d.lat,
            "lng": d.lng,
            "last_ping_at": d.last_ping_at.isoformat() if d.last_ping_at else None,
        }
        for d in drivers
    ]

    donations_stmt = (
        select(Donation)
        .where(Donation.status.in_([DonationStatus.POSTED, DonationStatus.MATCHING, DonationStatus.MATCHED, DonationStatus.IN_TRANSIT]))
        .limit(200)
    )
    donations = (await db.execute(donations_stmt)).scalars().all()
    donation_rows = [
        {
            "id": str(d.id),
            "status": d.status,
            "diet": d.diet,
            "total_portions": d.total_portions,
            "pickup_lat": d.pickup_lat,
            "pickup_lng": d.pickup_lng,
        }
        for d in donations
    ]

    alloc_counts = (
        await db.execute(
            select(Allocation.status, func.count(Allocation.id))
            .group_by(Allocation.status)
        )
    ).all()
    alloc_summary = {str(s): c for s, c in alloc_counts}

    active_routes_count = (
        await db.execute(
            select(func.count(Route.id)).where(Route.status.in_(["active", "planned"]))
        )
    ).scalar_one()

    from app.db.models.donor import Donor
    donors_res = (await db.execute(select(Donor).limit(100))).scalars().all()
    donor_rows = [
        {"id": str(dn.id), "org_name": dn.org_name, "lat": dn.lat, "lng": dn.lng}
        for dn in donors_res
    ]

    orgs_res = (await db.execute(select(RecipientOrg).limit(100))).scalars().all()
    org_rows = [
        {"id": str(o.id), "name": o.name, "lat": o.lat, "lng": o.lng, "need_level": o.need_level}
        for o in orgs_res
    ]
    orgs_count = len(org_rows)

    routes_res = (
        await db.execute(
            select(Route)
            .where(Route.status.in_(["active", "planned"]))
            .options(selectinload(Route.stops))
            .limit(100)
        )
    ).scalars().all()
    route_rows = [
        {"id": str(r.id), "driver_id": str(r.driver_id), "status": r.status, "stops_count": len(r.stops)}
        for r in routes_res
    ]

    return {
        "as_of": now_utc.isoformat(),
        "donors": donor_rows,
        "orgs": org_rows,
        "drivers": driver_rows,
        "routes": route_rows,
        "online_drivers": sum(1 for d in drivers if d.status != DriverStatus.OFFLINE),
        "active_routes": active_routes_count,
        "donations": donation_rows,
        "allocation_status_counts": alloc_summary,
        "orgs_total": orgs_count,
    }



# ---- Simulate donation ----

@router.post("/simulate/donation", summary="Fire test donations")
async def simulate_donation(
    req: SimulateDonationRequest,
    current_user=Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Create test donations and trigger dispatch. Scenarios: normal, wedding_night, rush_hour."""
    from app.db.models.donor import Donor

    donor_stmt = select(Donor).limit(1)
    donor = (await db.execute(donor_stmt)).scalar_one_or_none()
    if not donor:
        raise HTTPException(status_code=400, detail="No donors seeded. Run make seed first.")

    now = datetime.now(UTC)
    created_ids: list[str] = []

    if req.scenario == "wedding_night":
        portions_list = [300]
        diet = DietType.VEG
        prep_offset_h = -1
    elif req.scenario == "rush_hour":
        portions_list = [random.randint(20, 60) for _ in range(req.count)]
        diet = random.choice(list(DietType))
        prep_offset_h = -2
    else:
        portions_list = [random.randint(15, 50) for _ in range(req.count)]
        diet = DietType.VEG
        prep_offset_h = -1

    for portions in portions_list:
        lat, lng = random_offset_coords(settings.SEED_CENTER_LAT, settings.SEED_CENTER_LNG, 5.0)
        don = Donation(
            donor_id=donor.id,
            status=DonationStatus.POSTED,
            diet=diet,
            storage=StorageCondition.AMBIENT,
            category="cooked_meals",
            total_portions=portions,
            prepared_at=now + timedelta(hours=prep_offset_h),
            safe_until=now + timedelta(hours=4),
            pickup_window_start=now,
            pickup_window_end=now + timedelta(hours=2),
            pickup_lat=lat,
            pickup_lng=lng,
            pickup_address=f"Sim Pickup ({lat:.4f},{lng:.4f})",
            notes=f"Simulated donation - scenario={req.scenario}",
        )
        db.add(don)
        await db.flush()
        created_ids.append(str(don.id))

    await db.commit()

    # Trigger dispatch immediately using a fresh session
    try:
        async with async_session_maker() as dispatch_db:
            await dispatch_pending_tasks(dispatch_db, now)
            await dispatch_db.commit()
    except Exception as exc:
        logger.warning("simulate_dispatch_error", error=str(exc))

    logger.info("simulate_donation", scenario=req.scenario, count=len(created_ids))
    return {
        "scenario": req.scenario,
        "donations": created_ids,
        "created": created_ids,
    }


# ---- Chaos injection ----

@router.post("/chaos", summary="Chaos failure injection")
async def inject_chaos(
    req: ChaosRequest,
    _=Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Inject a failure scenario.
    Kinds: driver_drop | org_full | traffic_spike | osrm_down
    """
    kind = req.kind
    if kind == "osrm_down":
        settings.CHAOS_OSRM_DOWN = True
        return {"kind": kind, "status": "OSRM marked as down. Routing will use haversine fallback."}

    elif kind == "driver_drop":
        if req.target_id:
            driver_stmt = select(Driver).where(Driver.id == uuid.UUID(req.target_id))
        else:
            driver_stmt = select(Driver).where(Driver.status == DriverStatus.ON_TASK).limit(1)
        driver = (await db.execute(driver_stmt)).scalar_one_or_none()
        if not driver:
            raise HTTPException(status_code=404, detail="No matching driver found.")
        driver.last_ping_at = datetime.now(UTC) - timedelta(seconds=200)  # force stale
        driver.status = DriverStatus.STALE
        settings.CHAOS_DRIVER_DROP = True
        await db.commit()
        return {"kind": kind, "driver_id": str(driver.id), "status": "Driver marked stale."}

    elif kind == "org_full":
        if req.target_id:
            org_stmt = select(RecipientOrg).where(RecipientOrg.id == uuid.UUID(req.target_id))
        else:
            org_stmt = select(RecipientOrg).limit(1)
        org = (await db.execute(org_stmt)).scalar_one_or_none()
        if not org:
            raise HTTPException(status_code=404, detail="No matching org found.")
        org.is_open_override = False  # marks org as closed/full
        settings.CHAOS_ORG_FULL = True
        await db.commit()
        return {"kind": kind, "org_id": str(org.id), "status": "Org marked as full/closed."}

    elif kind == "traffic_spike":
        settings.CHAOS_TRAFFIC_SPIKE = True
        return {"kind": kind, "status": "Traffic spike active. Travel times doubled."}

    else:
        raise HTTPException(status_code=400, detail=f"Unknown chaos kind: {kind}. Use: driver_drop|org_full|traffic_spike|osrm_down")


# ---- Metrics ----

@router.get("/metrics", summary="Dispatch KPIs")
async def admin_metrics(
    _=Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Return operational dispatch KPIs."""
    now_utc = datetime.now(UTC)
    window_start = now_utc - timedelta(hours=24)

    # Deliveries in last 24h
    delivered_stmt = select(func.count(ImpactLedger.id)).where(
        ImpactLedger.delivered_at >= window_start
    )
    deliveries_24h = (await db.execute(delivered_stmt)).scalar_one()

    # Total meals in last 24h
    meals_stmt = select(func.coalesce(func.sum(ImpactLedger.meals), 0)).where(
        ImpactLedger.delivered_at >= window_start
    )
    meals_24h = (await db.execute(meals_stmt)).scalar_one()

    # Active routes
    active_routes = (
        await db.execute(
            select(func.count(Route.id)).where(Route.status.in_(["active", "planned"]))
        )
    ).scalar_one()

    # Online drivers
    online_drivers = (
        await db.execute(
            select(func.count(Driver.id)).where(
                Driver.status.in_([DriverStatus.AVAILABLE, DriverStatus.ON_TASK])
            )
        )
    ).scalar_one()

    # Pending allocations (not yet assigned)
    pending_dispatch = (
        await db.execute(
            select(func.count(Allocation.id)).where(
                Allocation.status.in_([AllocationStatus.ACCEPTED, AllocationStatus.DRIVER_PENDING])
            )
        )
    ).scalar_one()

    # Failed allocations in last 24h
    failed_stmt = (
        select(func.count(Allocation.id))
        .where(
            Allocation.status == AllocationStatus.FAILED,
            Allocation.updated_at >= window_start,
        )
    )
    failed_24h = (await db.execute(failed_stmt)).scalar_one()

    # Active donations count (non-terminal states)
    active_don_stmt = select(func.count(Donation.id)).where(
        Donation.status.in_([
            DonationStatus.POSTED,
            DonationStatus.MATCHING,
            DonationStatus.PARTIALLY_MATCHED,
            DonationStatus.MATCHED,
            DonationStatus.IN_TRANSIT,
        ])
    )
    active_donations = (await db.execute(active_don_stmt)).scalar_one()

    return {
        "as_of": now_utc.isoformat(),
        "window_hours": 24,
        "deliveries_24h": deliveries_24h,
        "meals_rescued_24h": int(meals_24h),
        "active_routes": active_routes,
        "online_drivers": online_drivers,
        "pending_dispatch": pending_dispatch,
        "failed_allocations_24h": failed_24h,
        "active_donations": active_donations,
        "chaos_flags": {
            "osrm_down": settings.CHAOS_OSRM_DOWN,
            "driver_drop": settings.CHAOS_DRIVER_DROP,
            "org_full": settings.CHAOS_ORG_FULL,
            "traffic_spike": settings.CHAOS_TRAFFIC_SPIKE,
        },
    }

