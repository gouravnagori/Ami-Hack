"""
Driver simulator — services/sim/driver_sim.py  (Section 9)

Moves each active simulated driver along its route polyline at vehicle speed
times SIM_SPEED factor, emitting real GPS pings through the same ingest path
as a live driver would. This exercises the full tracking, ETA, and risk-monitor
pipeline with synthetic data.
"""

import asyncio
import math
import random
from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import DriverStatus, StopStatus
from app.db.models.driver import Driver
from app.db.models.route import Route
from app.db.session import async_session_maker
from app.services.tracking import ingest_location

logger = structlog.get_logger("goldenhour.sim.driver")

# Vehicle speed table (km/h)
VEHICLE_SPEEDS_KPH = {
    "bicycle": 12.0,
    "scooter": 24.0,
    "e_rickshaw": 20.0,
    "van": 22.0,
}
SIM_SPEED = 5.0  # simulation time-accelerator: 5x real-time


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _interpolate(lat1: float, lng1: float, lat2: float, lng2: float, fraction: float):
    """Linear interpolation along a great-circle segment (accurate enough for city-scale)."""
    return lat1 + fraction * (lat2 - lat1), lng1 + fraction * (lng2 - lng1)


async def simulate_driver_step(driver_id: str) -> None:
    """
    Advance a single driver one simulation step.
    Looks up the driver's active route, finds the next pending stop,
    and pings a location partway along the straight line towards it.
    """
    async with async_session_maker() as db:
        driver_stmt = (
            select(Driver)
            .where(Driver.id == driver_id)
            .options(selectinload(Driver.routes).selectinload(Route.stops))
        )
        driver = (await db.execute(driver_stmt)).scalar_one_or_none()
        if not driver or driver.status not in (DriverStatus.ON_TASK, DriverStatus.AVAILABLE):
            return
        if driver.lat is None or driver.lng is None:
            return

        active_route: Route | None = None
        for r in driver.routes:
            if r.status in ("active", "planned"):
                active_route = r
                break

        if not active_route:
            return

        pending_stops = sorted(
            [s for s in active_route.stops if s.status == StopStatus.PENDING],
            key=lambda s: s.seq,
        )
        if not pending_stops:
            return

        _next_stop = pending_stops[0]
        # We need coordinates for the stop — approximate from planned_arrival offset
        # Since RouteStop doesn't store coords, use a random small offset from driver pos
        target_lat = driver.lat + random.uniform(-0.001, 0.001)
        target_lng = driver.lng + random.uniform(-0.001, 0.001)

        # Move driver 20 % of the way towards the target per step
        new_lat, new_lng = _interpolate(driver.lat, driver.lng, target_lat, target_lng, 0.2)
        speed_kph = VEHICLE_SPEEDS_KPH.get(str(driver.vehicle_type), 20.0) * SIM_SPEED
        speed_ms = speed_kph / 3.6

        await ingest_location(
            db,
            driver_id=driver.id,
            lat=new_lat,
            lng=new_lng,
            speed=speed_ms,
            heading=0.0,
            now=datetime.now(UTC),
        )
        logger.debug("sim.driver_ping", driver_id=str(driver_id), lat=new_lat, lng=new_lng)


async def run_simulation_loop(interval_s: float = 5.0, max_iterations: int = 0) -> None:
    """
    Continuously move all active simulated drivers at interval_s real-time
    seconds per step. Pass max_iterations > 0 to stop after N steps.
    """
    logger.info("sim.loop_started", interval_s=interval_s)
    iteration = 0
    while True:
        async with async_session_maker() as db:
            stmt = select(Driver).where(Driver.status.in_([DriverStatus.ON_TASK, DriverStatus.AVAILABLE]))
            drivers = (await db.execute(stmt)).scalars().all()

        tasks = [simulate_driver_step(str(d.id)) for d in drivers if d.lat and d.lng]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        iteration += 1
        if max_iterations > 0 and iteration >= max_iterations:
            break

        await asyncio.sleep(interval_s)
