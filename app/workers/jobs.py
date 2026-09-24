"""
ARQ background jobs — workers/jobs.py  (Section 8)

All jobs are:
  - Idempotent: safe to run twice (state checks guard re-execution).
  - Restart-safe: timers are ARQ delayed jobs, not in-memory asyncio.
  - Logging: each job logs duration and outcome via structlog.

Jobs:
  dispatch_tick        (every DISPATCH_TICK_SECONDS=10)
  offer_expiry         (delayed per offer — expire a single offer)
  risk_monitor         (every RISK_MONITOR_SECONDS=15)
  stale_driver_check   (every 30 s)
  capacity_tick        (every 60 s, refresh capacity projections)
  notify               (on-demand, sends a single notification)
"""

import time
from datetime import UTC, datetime

import structlog

logger = structlog.get_logger("goldenhour.workers")


async def dispatch_tick(ctx: dict) -> str:
    """
    Run the full dispatch cycle: load pending tasks, find drivers,
    create driver offers with route previews.

    Run every DISPATCH_TICK_SECONDS via ARQ cron or self-enqueue.
    """
    t0 = time.monotonic()
    from app.db.session import async_session_maker
    from app.services.dispatch.engine import dispatch_pending_tasks

    now = datetime.now(UTC)
    async with async_session_maker() as db:
        try:
            offer_ids = await dispatch_pending_tasks(db, now)
            await db.commit()
            elapsed = round(time.monotonic() - t0, 3)
            logger.info("dispatch_tick.done", offers_created=len(offer_ids), elapsed_s=elapsed)
            return f"created {len(offer_ids)} offers in {elapsed}s"
        except Exception as exc:
            await db.rollback()
            logger.error("dispatch_tick.error", error=str(exc))
            return f"error: {exc}"


async def offer_expiry(ctx: dict, offer_id: str) -> str:
    """
    Expire a single offer: set status=expired, release any held capacity
    reservation, and cascade to next offer in matching queue if applicable.

    Enqueued with a delay equal to the offer TTL when the offer is created.
    Idempotent: no-op if offer is already expired/accepted/declined.
    """
    import uuid

    from sqlalchemy import select

    from app.core.config import OfferKind, OfferStatus
    from app.db.models.capacity import CapacityReservation
    from app.db.models.offer import Offer
    from app.db.session import async_session_maker
    from app.services.capacity import release_reservation

    async with async_session_maker() as db:
        try:
            stmt = (
                select(Offer)
                .where(Offer.id == uuid.UUID(offer_id))
                .with_for_update()
            )
            offer = (await db.execute(stmt)).scalar_one_or_none()
            if not offer:
                return f"offer {offer_id} not found"
            if offer.status != OfferStatus.PENDING:
                return f"offer {offer_id} already {offer.status}"

            offer.status = OfferStatus.EXPIRED
            offer.responded_at = datetime.now(UTC)

            # Release capacity reservation for recipient offers
            if offer.kind == OfferKind.RECIPIENT and offer.allocation_id:
                res_stmt = select(CapacityReservation).where(
                    CapacityReservation.allocation_id == offer.allocation_id,
                    CapacityReservation.state == "held",
                )
                reservations = (await db.execute(res_stmt)).scalars().all()
                for res in reservations:
                    await release_reservation(db, res.id)

            await db.commit()
            logger.info("offer_expiry.done", offer_id=offer_id, kind=str(offer.kind))
            return f"expired offer {offer_id}"
        except Exception as exc:
            await db.rollback()
            logger.error("offer_expiry.error", offer_id=offer_id, error=str(exc))
            return f"error: {exc}"


async def risk_monitor(ctx: dict) -> str:
    """
    Every RISK_MONITOR_SECONDS=15: for each active route, recompute
    predicted_arrival and emit alert.risk events on transitions.

    Note: actual ETA refresh happens in tracking.ingest_location (on GPS ping).
    This job handles the batch check for routes that haven't had a recent ping.
    """
    t0 = time.monotonic()

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.core.config import StopStatus
    from app.db.models.route import Route
    from app.db.session import async_session_maker
    from app.services.capacity import ensure_utc
    from app.services.routing.eta import classify_risk

    now = datetime.now(UTC)
    alerts: list[dict] = []

    async with async_session_maker() as db:
        try:
            route_stmt = (
                select(Route)
                .where(Route.status.in_(["active", "planned"]))
                .options(selectinload(Route.stops))
            )
            routes = (await db.execute(route_stmt)).scalars().all()

            for route in routes:
                pending = [s for s in route.stops if s.status in (StopStatus.PENDING, StopStatus.ARRIVED)]
                for stop in pending:
                    if not stop.window_end or not stop.predicted_arrival:
                        continue
                    pred = ensure_utc(stop.predicted_arrival)
                    wend = ensure_utc(stop.window_end)
                    if not pred or not wend:
                        continue
                    slack_s = (wend - pred).total_seconds()
                    window_s = max(60.0, (wend - now).total_seconds())
                    risk = classify_risk(slack_s, window_s)
                    if risk == "critical":
                        alerts.append({
                            "stop_id": str(stop.id),
                            "allocation_id": str(stop.allocation_id),
                            "risk": risk,
                            "slack_seconds": round(slack_s, 1),
                        })

            elapsed = round(time.monotonic() - t0, 3)
            logger.info("risk_monitor.done", alerts=len(alerts), routes=len(routes), elapsed_s=elapsed)
            return f"checked {len(routes)} routes, {len(alerts)} critical"
        except Exception as exc:
            logger.error("risk_monitor.error", error=str(exc))
            return f"error: {exc}"


async def stale_driver_check(ctx: dict) -> str:
    """
    Every 30 s: mark drivers STALE if no ping > STALE_DRIVER_SECONDS,
    and release their stops if silent > STALE_DRIVER_REASSIGN_SECONDS.
    """
    from app.db.session import async_session_maker
    from app.services.tracking import stale_driver_check as _check

    async with async_session_maker() as db:
        try:
            affected = await _check(db)
            logger.info("stale_driver_check.done", affected=len(affected))
            return f"affected {len(affected)} drivers"
        except Exception as exc:
            logger.error("stale_driver_check.error", error=str(exc))
            return f"error: {exc}"


async def capacity_tick(ctx: dict) -> str:
    """
    Every 60 s: expire stale capacity reservations whose held_until has passed.
    Idempotent — only updates rows in 'held' state past their deadline.
    """
    from sqlalchemy import select

    from app.core.config import settings
    from app.db.models.capacity import CapacityReservation
    from app.db.session import async_session_maker

    now = datetime.now(UTC)
    async with async_session_maker() as db:
        try:
            stmt = select(CapacityReservation).where(
                CapacityReservation.state == "held",
                CapacityReservation.held_until < now,
            )
            if "postgres" in str(settings.DATABASE_URL):
                stmt = stmt.with_for_update(skip_locked=True)
            expired = (await db.execute(stmt)).scalars().all()
            for res in expired:
                res.state = "released"
            if expired:
                await db.commit()
            logger.info("capacity_tick.done", expired=len(expired))
            return f"released {len(expired)} expired reservations"
        except Exception as exc:
            await db.rollback()
            logger.error("capacity_tick.error", error=str(exc))
            return f"error: {exc}"


async def notify(ctx: dict, user_id: str, template: str, data: dict) -> str:
    """
    On-demand notification job. Retried with backoff by ARQ on failure.
    """
    from app.services.notifications.base import notification_service

    try:
        await notification_service.send(user_id=user_id, template=template, data=data)
        return f"notified {user_id} template={template}"
    except Exception as exc:
        logger.error("notify.error", user_id=user_id, template=template, error=str(exc))
        raise  # Let ARQ retry
