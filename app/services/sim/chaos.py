"""
Chaos module — services/sim/chaos.py  (Section 9)

Provides service-layer helpers for the chaos endpoints.
Resets chaos flags and restores the system to a clean state.
"""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import DriverStatus, settings
from app.db.models.driver import Driver
from app.db.models.recipient import RecipientOrg

logger = structlog.get_logger("goldenhour.sim.chaos")


async def reset_all_chaos(db: AsyncSession) -> dict:
    """
    Reset all chaos flags and attempt to restore affected entities.
    Returns a summary of what was reset.
    """
    reset_summary: dict[str, str] = {}

    if settings.CHAOS_OSRM_DOWN:
        settings.CHAOS_OSRM_DOWN = False
        reset_summary["osrm_down"] = "OSRM restored to primary provider"

    if settings.CHAOS_TRAFFIC_SPIKE:
        settings.CHAOS_TRAFFIC_SPIKE = False
        reset_summary["traffic_spike"] = "Traffic factor reset to normal"

    if settings.CHAOS_ORG_FULL:
        settings.CHAOS_ORG_FULL = False
        # Re-open all orgs that were closed by chaos
        stmt = select(RecipientOrg).where(RecipientOrg.is_open_override.is_(False))
        orgs = (await db.execute(stmt)).scalars().all()
        for org in orgs:
            org.is_open_override = None
        if orgs:
            await db.commit()
        reset_summary["org_full"] = f"Re-opened {len(orgs)} org(s)"

    if settings.CHAOS_DRIVER_DROP:
        settings.CHAOS_DRIVER_DROP = False
        # Restore stale drivers to available
        stmt = select(Driver).where(Driver.status == DriverStatus.STALE)
        drivers = (await db.execute(stmt)).scalars().all()
        for d in drivers:
            d.status = DriverStatus.AVAILABLE
        if drivers:
            await db.commit()
        reset_summary["driver_drop"] = f"Restored {len(drivers)} stale driver(s)"

    logger.info("chaos.reset", summary=reset_summary)
    return reset_summary


def get_active_chaos_flags() -> dict:
    """Return the current chaos flag state."""
    return {
        "osrm_down": settings.CHAOS_OSRM_DOWN,
        "driver_drop": settings.CHAOS_DRIVER_DROP,
        "org_full": settings.CHAOS_ORG_FULL,
        "traffic_spike": settings.CHAOS_TRAFFIC_SPIKE,
    }
