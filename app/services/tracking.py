"""
GPS ingestion, ETA refresh, and risk monitoring — services/tracking.py

Stage 6 (Live tracking and re-optimisation):
- ingest_location: consume a GPS ping, update driver.lat/lng, refresh
  predicted_arrival for all active stops, detect risk transitions.
- stale_driver_check: marks drivers STALE if no ping for STALE_DRIVER_SECONDS,
  re-dispatches their not-yet-started stops at STALE_DRIVER_REASSIGN_SECONDS.
"""

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import (
    AllocationStatus,
    DriverStatus,
    StopStatus,
    StopType,
    settings,
)
from app.db.models.allocation import Allocation
from app.db.models.driver import Driver, DriverLocation
from app.db.models.route import Route, RouteStop
from app.services.capacity import ensure_utc
from app.services.routing.client import routing_client
from app.services.routing.eta import classify_risk

logger = structlog.get_logger("goldenhour.tracking")


async def ingest_location(
    session: AsyncSession,
    driver_id: uuid.UUID,
    lat: float,
    lng: float,
    speed: float = 0.0,
    heading: float = 0.0,
    now: datetime | None = None,
) -> dict:
    """
    Process a GPS ping from a driver.
    1. Update driver.lat, driver.lng, driver.last_ping_at.
    2. Append to driver_locations table.
    3. For each active stop on the driver's active route, recompute
       predicted_arrival using OSRM (or haversine fallback).
    4. Detect and return any risk transitions.
    """
    now_utc = ensure_utc(now) or datetime.now(UTC)

    driver_stmt = select(Driver).where(Driver.id == driver_id).with_for_update()
    driver = (await session.execute(driver_stmt)).scalar_one_or_none()
    if not driver:
        return {"status": "driver_not_found"}

    old_status = driver.status
    driver.lat = lat
    driver.lng = lng
    driver.last_ping_at = now_utc
    if old_status == DriverStatus.STALE:
        driver.status = DriverStatus.ON_TASK

    loc_row = DriverLocation(
        driver_id=driver_id,
        lat=lat,
        lng=lng,
        speed=speed,
        heading=heading,
        at=now_utc,
    )
    session.add(loc_row)

    # Load active route + stops with full allocation context
    route_stmt = (
        select(Route)
        .where(Route.driver_id == driver_id, Route.status.in_(["active", "planned"]))
        .options(
            selectinload(Route.stops)
            .selectinload(RouteStop.allocation)
            .selectinload(Allocation.donation),
            selectinload(Route.stops)
            .selectinload(RouteStop.allocation)
            .selectinload(Allocation.recipient),
        )
        .order_by(Route.created_at.desc())
        .limit(1)
    )
    route = (await session.execute(route_stmt)).scalar_one_or_none()

    risk_alerts: list[dict] = []
    if route:
        pending_stops = [
            s for s in route.stops
            if s.status in (StopStatus.PENDING, StopStatus.ARRIVED)
        ]
        pending_stops.sort(key=lambda s: s.seq)

        cursor_lat, cursor_lng = lat, lng
        cursor_t = now_utc

        for stop in pending_stops:
            alloc = stop.allocation
            if not alloc:
                continue

            # Determine stop coordinates from the allocation context
            if stop.type == StopType.PICKUP:
                don = alloc.donation
                stop_lat = don.pickup_lat if don else cursor_lat
                stop_lng = don.pickup_lng if don else cursor_lng
            else:
                recip = alloc.recipient
                stop_lat = recip.lat if recip else cursor_lat
                stop_lng = recip.lng if recip else cursor_lng

            try:
                _dist_m, dur_s, _poly = await routing_client.get_route(
                    [(cursor_lat, cursor_lng), (stop_lat, stop_lng)],
                    vehicle=driver.vehicle_type,
                    dt=cursor_t,
                )
                new_pred = cursor_t + timedelta(seconds=dur_s)
            except Exception:
                new_pred = cursor_t + timedelta(minutes=10)

            old_pred = ensure_utc(stop.predicted_arrival)
            stop.predicted_arrival = new_pred

            # Classify risk for this stop
            if stop.window_end:
                wend = ensure_utc(stop.window_end)
                slack_s = (wend - new_pred).total_seconds() if wend else 0.0
                window_s = max(60.0, (wend - now_utc).total_seconds()) if wend else 60.0
                new_risk = classify_risk(slack_s, window_s)

                old_slack_s = (ensure_utc(stop.window_end) - old_pred).total_seconds() if (old_pred and ensure_utc(stop.window_end)) else None
                old_risk = classify_risk(old_slack_s, window_s) if old_slack_s is not None else None

                if old_risk != new_risk:
                    risk_alerts.append({
                        "stop_id": str(stop.id),
                        "allocation_id": str(stop.allocation_id),
                        "old_risk": old_risk,
                        "new_risk": new_risk,
                        "slack_seconds": round(slack_s, 1),
                    })
                    logger.warning(
                        "risk_transition",
                        stop_id=str(stop.id),
                        old=old_risk,
                        new=new_risk,
                    )

            cursor_lat, cursor_lng = stop_lat, stop_lng
            cursor_t = new_pred

    await session.commit()
    return {"status": "ok", "risk_alerts": risk_alerts}


async def stale_driver_check(session: AsyncSession, now: datetime | None = None) -> list[str]:
    """
    Mark drivers STALE if no ping for STALE_DRIVER_SECONDS.
    At STALE_DRIVER_REASSIGN_SECONDS, release their not-yet-started stops.
    Returns list of affected driver IDs.
    """
    now_utc = ensure_utc(now) or datetime.now(UTC)
    stale_threshold = now_utc - timedelta(seconds=settings.STALE_DRIVER_SECONDS)
    reassign_threshold = now_utc - timedelta(seconds=settings.STALE_DRIVER_REASSIGN_SECONDS)

    active_stmt = select(Driver).where(
        Driver.status.in_([DriverStatus.AVAILABLE, DriverStatus.ON_TASK, DriverStatus.STALE]),
        Driver.last_ping_at.isnot(None),
    )
    drivers = (await session.execute(active_stmt)).scalars().all()

    affected: list[str] = []
    for driver in drivers:
        last_ping = ensure_utc(driver.last_ping_at)
        if not last_ping:
            continue

        if last_ping < reassign_threshold and driver.status == DriverStatus.STALE:
            # Release not-yet-started stops and reset allocations for re-dispatch
            route_stmt = (
                select(Route)
                .where(Route.driver_id == driver.id, Route.status.in_(["active", "planned"]))
                .options(selectinload(Route.stops).selectinload(RouteStop.allocation))
            )
            routes = (await session.execute(route_stmt)).scalars().all()
            for route in routes:
                for stop in route.stops:
                    if stop.status == StopStatus.PENDING and stop.type == StopType.PICKUP:
                        stop.status = StopStatus.FAILED
                        if stop.allocation:
                            stop.allocation.status = AllocationStatus.ACCEPTED
                            stop.allocation.driver_id = None
                route.status = "cancelled"

            driver.status = DriverStatus.OFFLINE
            affected.append(str(driver.id))
            logger.warning("stale_driver_reassigned", driver_id=str(driver.id))

        elif last_ping < stale_threshold and driver.status not in (DriverStatus.OFFLINE, DriverStatus.STALE):
            driver.status = DriverStatus.STALE
            affected.append(str(driver.id))
            logger.warning("stale_driver_marked", driver_id=str(driver.id))

    if affected:
        await session.commit()
    return affected
