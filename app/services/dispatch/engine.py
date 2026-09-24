"""
Dispatch Engine Orchestrator.

Orchestrates Stages 0 through 5:
- Trigger pending allocations needing driver assignment
- Loads telematics-aware candidate drivers
- Runs Stage 3 (stacking insertion) and Stage 2 (SciPy bipartite matching)
- Chooses lowest-cost assignment
- Runs Stage 4 (OR-Tools PDPTW) if route has >= 3 stops
- Dispatches Stage 5 Driver Offers with route preview and TTL (45s normal / 25s priority)
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import (
    AllocationStatus,
    DietType,
    DriverStatus,
    OfferKind,
    OfferStatus,
    Risk,
    StopStatus,
    StopType,
    StorageCondition,
)
from app.db.models.allocation import Allocation
from app.db.models.donation import Donation
from app.db.models.driver import Driver
from app.db.models.offer import Offer
from app.db.models.route import Route, RouteStop
from app.services.capacity import ensure_utc
from app.services.dispatch.assignment import (
    compute_driver_task_cost,
    filter_candidate_drivers,
    solve_bipartite_assignment,
)
from app.services.dispatch.insertion import find_best_stacked_insertion
from app.services.dispatch.types import (
    AssignmentResult,
    DispatchTask,
    DriverCandidate,
    InsertionResult,
    StopPlan,
)
from app.services.dispatch.vrp import optimize_route_pdptw
from app.services.routing.client import routing_client


async def load_pending_dispatch_tasks(
    session: AsyncSession, now: datetime
) -> list[DispatchTask]:
    """
    Find allocations that need a driver:
    Status is ACCEPTED or DRIVER_PENDING, no driver assigned yet,
    and no pending active driver offer.
    """
    now_utc = ensure_utc(now) or datetime.now(UTC)

    stmt = (
        select(Allocation)
        .where(
            Allocation.status.in_([AllocationStatus.ACCEPTED, AllocationStatus.DRIVER_PENDING]),
            Allocation.driver_id.is_(None),
        )
        .options(
            selectinload(Allocation.donation).selectinload(Donation.donor),
            selectinload(Allocation.recipient),
            selectinload(Allocation.offers),
        )
    )
    result = await session.execute(stmt)
    allocs = result.scalars().all()

    tasks: list[DispatchTask] = []
    for alloc in allocs:
        # Check if an active unexpired driver offer is already pending
        has_pending_driver_offer = any(
            o.kind == OfferKind.DRIVER
            and o.status == OfferStatus.PENDING
            and ensure_utc(o.expires_at) > now_utc
            for o in alloc.offers
        )
        if has_pending_driver_offer:
            continue

        don = alloc.donation
        donor = don.donor if don else None
        recip = alloc.recipient

        if not don or not donor or not recip:
            continue

        deadline = ensure_utc(alloc.deadline) or (now_utc + timedelta(hours=3))
        ready_at = ensure_utc(don.pickup_window_start) or now_utc
        latest_pickup = ensure_utc(don.pickup_window_end) or (now_utc + timedelta(hours=2))
        dropoff_window_end = deadline

        slack_s = max(0.0, (deadline - now_utc).total_seconds())
        window_s = max(60.0, (deadline - ready_at).total_seconds())
        slack_ratio = min(1.0, slack_s / window_s)

        risk = Risk.SAFE
        if slack_ratio < 0.15:
            risk = Risk.CRITICAL
        elif slack_ratio < 0.30:
            risk = Risk.TIGHT

        task = DispatchTask(
            allocation_id=alloc.id,
            donation_id=don.id,
            portions=alloc.portions,
            diet=DietType(don.diet),
            storage=StorageCondition(don.storage),
            container_label=alloc.container_label,
            deadline=deadline,
            pickup_lat=don.pickup_lat,
            pickup_lng=don.pickup_lng,
            pickup_address=don.pickup_address,
            pickup_name=donor.org_name,
            ready_at=ready_at,
            latest_pickup=latest_pickup,
            dropoff_lat=recip.lat,
            dropoff_lng=recip.lng,
            dropoff_address=recip.address,
            dropoff_name=recip.name,
            dropoff_window_end=dropoff_window_end,
            slack_seconds=slack_s,
            slack_ratio=slack_ratio,
            risk=risk,
        )
        tasks.append(task)

    return tasks


async def load_candidate_drivers(
    session: AsyncSession, now: datetime
) -> list[DriverCandidate]:
    """Load all online drivers with their active routes and pending stops."""
    stmt = (
        select(Driver)
        .where(Driver.status.in_([DriverStatus.AVAILABLE, DriverStatus.ON_TASK]))
        .options(
            selectinload(Driver.routes).selectinload(Route.stops).selectinload(RouteStop.allocation)
        )
    )
    result = await session.execute(stmt)
    drivers = result.scalars().all()

    candidates: list[DriverCandidate] = []
    for d in drivers:
        if d.lat is None or d.lng is None:
            continue

        active_route: Route | None = None
        existing_stops: list[StopPlan] = []
        for r in d.routes:
            if r.status in ("active", "planned"):
                active_route = r
                for s in r.stops:
                    if s.status in (StopStatus.PENDING, StopStatus.ARRIVED):
                        alloc = s.allocation
                        stop_plan = StopPlan(
                            id=s.id,
                            seq=s.seq,
                            type=s.type,
                            allocation_id=s.allocation_id,
                            lat=d.lat,  # will be populated from alloc
                            lng=d.lng,
                            window_start=s.window_start,
                            window_end=s.window_end,
                            planned_arrival=s.planned_arrival,
                            predicted_arrival=s.predicted_arrival,
                            portions=alloc.portions if alloc else 0,
                            requires_otp=True,
                        )
                        existing_stops.append(stop_plan)
                break

        candidate = DriverCandidate(
            id=d.id,
            user_id=d.user_id,
            vehicle_type=d.vehicle_type,
            capacity_portions=d.capacity_portions,
            has_cold_box=d.has_cold_box,
            status=d.status,
            lat=d.lat,
            lng=d.lng,
            last_ping_at=d.last_ping_at,
            accept_rate_ewma=d.accept_rate_ewma,
            speed_factor_ewma=d.speed_factor_ewma,
            service_radius_m=d.service_radius_m,
            active_route_id=active_route.id if active_route else None,
            existing_stops=existing_stops,
        )
        candidates.append(candidate)

    return candidates


async def dispatch_pending_tasks(
    session: AsyncSession, now: datetime
) -> list[uuid.UUID]:
    """
    Main dispatch cycle:
    1. Loads pending tasks & candidate drivers
    2. Runs Stage 3 (insertion stacking) and Stage 2 (SciPy bipartite assignment)
    3. Picks lowest cost assignment
    4. Runs Stage 4 VRP if route has >= 3 stops
    5. Creates driver offer with route preview and TTL
    Returns list of created offer IDs.
    """
    now_utc = ensure_utc(now) or datetime.now(UTC)
    tasks = await load_pending_dispatch_tasks(session, now_utc)
    if not tasks:
        return []

    drivers = await load_candidate_drivers(session, now_utc)
    if not drivers:
        return []

    driver_map = {d.id: d for d in drivers}
    created_offer_ids: list[uuid.UUID] = []

    # Map allocations
    alloc_ids = [t.allocation_id for t in tasks]
    alloc_res = await session.execute(select(Allocation).where(Allocation.id.in_(alloc_ids)))
    alloc_map = {a.id: a for a in alloc_res.scalars().all()}

    # Separate active vs idle drivers
    active_drivers = [d for d in drivers if d.existing_stops]
    idle_drivers = [d for d in drivers if not d.existing_stops and d.status == DriverStatus.AVAILABLE]

    # Pre-solve idle driver assignment via SciPy
    idle_assignments = solve_bipartite_assignment(tasks, idle_drivers, now_utc)
    idle_map: dict[uuid.UUID, AssignmentResult] = {a.task_id: a for a in idle_assignments}

    for task in tasks:
        alloc = alloc_map.get(task.allocation_id)
        if not alloc:
            continue

        # Try Stage 3: Stacked insertion on an active driver
        insertion_result: InsertionResult | None = None
        if active_drivers:
            insertion_result = find_best_stacked_insertion(task, active_drivers, now_utc)

        idle_result = idle_map.get(task.allocation_id)

        # Compare costs between idle vs stacked
        chosen_driver_id: uuid.UUID | None = None
        is_stacked = False
        stops_to_plan: list[StopPlan] = []

        if insertion_result and idle_result:
            if insertion_result.cost_minutes <= idle_result.cost_minutes:
                chosen_driver_id = insertion_result.driver_id
                is_stacked = True
                stops_to_plan = insertion_result.new_stops
            else:
                chosen_driver_id = idle_result.driver_id
                is_stacked = False
        elif insertion_result:
            chosen_driver_id = insertion_result.driver_id
            is_stacked = True
            stops_to_plan = insertion_result.new_stops
        elif idle_result:
            chosen_driver_id = idle_result.driver_id
            is_stacked = False
        else:
            # Fallback: single candidate check
            survivors = filter_candidate_drivers(task, drivers, now_utc)
            if survivors:
                best_d = survivors[0]
                cost, _, pred_del = compute_driver_task_cost(best_d, task, now_utc)
                if cost < 1e5:
                    chosen_driver_id = best_d.id
                    is_stacked = False

        if not chosen_driver_id:
            continue

        chosen_driver = driver_map[chosen_driver_id]

        # Build stop sequence if not already stacked
        if not is_stacked:
            pickup_stop = StopPlan(
                id=uuid.uuid4(),
                seq=1,
                type=StopType.PICKUP,
                allocation_id=task.allocation_id,
                lat=task.pickup_lat,
                lng=task.pickup_lng,
                name=task.pickup_name,
                address=task.pickup_address,
                window_start=task.ready_at,
                window_end=task.latest_pickup,
                portions=task.portions,
                diet=task.diet,
                storage=task.storage,
                container_label=task.container_label,
                requires_otp=True,
            )
            dropoff_stop = StopPlan(
                id=uuid.uuid4(),
                seq=2,
                type=StopType.DROPOFF,
                allocation_id=task.allocation_id,
                lat=task.dropoff_lat,
                lng=task.dropoff_lng,
                name=task.dropoff_name,
                address=task.dropoff_address,
                window_start=task.ready_at,
                window_end=task.dropoff_window_end,
                portions=task.portions,
                diet=task.diet,
                storage=task.storage,
                container_label=task.container_label,
                requires_otp=True,
            )
            stops_to_plan = [pickup_stop, dropoff_stop]

        # Stage 4: Run OR-Tools PDPTW if route has >= 3 stops
        saved_seconds = 0.0
        replanned_reason = "initial_dispatch"
        if len(stops_to_plan) >= 3:
            stops_to_plan, saved_seconds, replanned_reason = optimize_route_pdptw(
                chosen_driver, stops_to_plan, now_utc
            )

        # Get road polyline and accurate distance from OSRM
        waypoints = [(chosen_driver.lat, chosen_driver.lng)] + [
            (s.lat, s.lng) for s in stops_to_plan
        ]
        total_dist_m, total_dur_s, polyline = await routing_client.get_route(
            waypoints, vehicle=chosen_driver.vehicle_type, dt=now_utc
        )

        # Stage 5: TTL calculation: 45s normal, 25s priority (slack_ratio < 0.25)
        is_priority = task.slack_ratio < 0.25
        ttl_seconds = 25 if is_priority else 45
        offer_expires_at = now_utc + timedelta(seconds=ttl_seconds)

        # Route preview for driver app
        route_preview = {
            "driver_id": str(chosen_driver.id),
            "allocation_id": str(task.allocation_id),
            "stops_count": len(stops_to_plan),
            "is_stacked": is_stacked,
            "total_distance_m": round(total_dist_m, 1),
            "total_duration_s": round(total_dur_s, 1),
            "polyline": polyline,
            "stops": [
                {
                    "seq": s.seq,
                    "type": s.type,
                    "name": s.name,
                    "address": s.address,
                    "portions": s.portions,
                    "diet": s.diet,
                    "storage": s.storage,
                    "container_label": s.container_label,
                    "window_end": s.window_end.isoformat() if s.window_end else None,
                }
                for s in stops_to_plan
            ],
            "replanned_reason": replanned_reason,
            "saved_seconds_vs_previous": saved_seconds,
        }

        # Create Driver Offer
        driver_offer = Offer(
            kind=OfferKind.DRIVER,
            allocation_id=alloc.id,
            target_user_id=chosen_driver.user_id,
            status=OfferStatus.PENDING,
            expires_at=offer_expires_at,
            score=100.0,
            route_preview=route_preview,
        )
        session.add(driver_offer)

        alloc.status = AllocationStatus.DRIVER_PENDING
        created_offer_ids.append(driver_offer.id)

    await session.flush()
    return created_offer_ids
