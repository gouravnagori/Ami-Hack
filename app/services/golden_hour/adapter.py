"""
Golden Hour Intelligence Adapter — adapter.py

Clean integration boundary between Ami-Hack backend and Golden Hour FoodRescueEngine.
The backend converts application state into intelligence input, invokes the engine,
and returns a business-level result for persistence.
"""

import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Add Golden Hour intelligence engine to path
_GH_ROOT = Path(__file__).resolve().parents[4]  # x:\Golden Hour
if str(_GH_ROOT) not in sys.path:
    sys.path.insert(0, str(_GH_ROOT))

from food_rescue_engine.engine import FoodRescueEngine
from food_rescue_engine.domain.rescue_plan import RescuePlan

from app.db.models.donation import Donation, DonationItem
from app.db.models.driver import Driver
from app.db.models.recipient import RecipientOrg
from app.core.config import DriverStatus as AmiDriverStatus, DonationStatus
from app.services.golden_hour.mapper import (
    map_donation_to_gh,
    map_driver_to_gh,
    map_recipient_to_gh,
    km_to_metres,
    minutes_to_seconds,
)

logger = logging.getLogger("goldenhour.adapter")


class GoldenHourAdapter:
    """
    Clean boundary: Ami-Hack backend → Golden Hour Intelligence.

    Usage:
        adapter = GoldenHourAdapter()
        plan = await adapter.optimize_donation(session, donation_id)
    """

    def __init__(self):
        self._engine: Optional[FoodRescueEngine] = None

    def _get_engine(self) -> FoodRescueEngine:
        """Lazy-initialize the intelligence engine."""
        if self._engine is None:
            self._engine = FoodRescueEngine()
        return self._engine

    async def optimize_donation(
        self,
        session: AsyncSession,
        donation_id: str,
    ) -> Optional[dict]:
        """
        Main integration path:
        1. Load real donation from DB
        2. Load available drivers from DB
        3. Load recipient orgs from DB
        4. Map to GH domain models
        5. Invoke FoodRescueEngine
        6. Return business-level plan dict

        Returns None if optimization fails or no feasible plan found.
        """
        now = datetime.now(timezone.utc)

        # 1. Load donation with items
        import uuid as _uuid
        don_uuid = _uuid.UUID(donation_id) if isinstance(donation_id, str) else donation_id
        stmt = (
            select(Donation)
            .where(Donation.id == don_uuid)
            .options(selectinload(Donation.items))
        )
        result = await session.execute(stmt)
        donation = result.scalar_one_or_none()
        if donation is None:
            logger.warning("optimize: donation %s not found", donation_id)
            return None

        # 2. Load available drivers
        driver_stmt = select(Driver).where(
            Driver.status.in_([AmiDriverStatus.AVAILABLE]),
            Driver.lat.is_not(None),
            Driver.lng.is_not(None),
        )
        driver_result = await session.execute(driver_stmt)
        ami_drivers = driver_result.scalars().all()

        # 3. Load recipient orgs
        org_stmt = select(RecipientOrg)
        org_result = await session.execute(org_stmt)
        ami_orgs = org_result.scalars().all()

        # 4. Map to Golden Hour domain models
        gh_donation = map_donation_to_gh(donation, list(donation.items))

        gh_drivers = []
        for d in ami_drivers:
            gh_d = map_driver_to_gh(d)
            if gh_d is not None:
                gh_drivers.append(gh_d)

        gh_recipients = [map_recipient_to_gh(o) for o in ami_orgs]

        if not gh_drivers:
            logger.warning("optimize: no available drivers")
            return {"status": "NO_AVAILABLE_DRIVERS", "plan": None}

        if not gh_recipients:
            logger.warning("optimize: no recipients")
            return {"status": "NO_RECIPIENTS", "plan": None}

        # 5. Invoke the engine
        try:
            engine = self._get_engine()
            plan: RescuePlan = engine.optimize(
                donation=gh_donation,
                drivers=gh_drivers,
                recipients=gh_recipients,
                current_time=now,
            )
        except Exception as e:
            logger.error("optimize: engine error: %s", str(e))
            return {"status": "OPTIMIZATION_FAILED", "error": str(e), "plan": None}

        if plan is None:
            return {"status": "NO_FEASIBLE_PLAN", "plan": None}

        # 6. Convert back to business-level dict
        return {
            "status": "SUCCESS",
            "plan": {
                "plan_id": plan.plan_id,
                "donation_id": plan.donation_id,
                "driver_id": plan.driver_id,
                "allocations": [
                    {
                        "recipient_id": a.recipient_id,
                        "quantity_kg": a.quantity_kg,
                    }
                    for a in plan.allocations
                ],
                "total_distance_m": km_to_metres(plan.total_distance_km),
                "total_duration_s": minutes_to_seconds(plan.total_duration_minutes),
                "estimated_pickup_time": plan.estimated_pickup_time.isoformat(),
                "estimated_delivery_time": plan.estimated_delivery_time.isoformat(),
                "remaining_safe_minutes": plan.remaining_safe_minutes,
                "feasibility_status": plan.feasibility_status,
                "expected_rescued_kg": plan.expected_rescued_kg,
                "solver_status": plan.solver_status,
                "explanation": plan.explanation,
            },
        }


# Singleton instance
golden_hour_adapter = GoldenHourAdapter()
