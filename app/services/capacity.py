"""
Capacity engine — time-aware projection and reservation-based ledger.

Enforces:
- R1: Quantity <= available capacity at the driver's ETA
- R5: Capacity changes over time (service rate projection + manual updates)
- R6: No double-booking (concurrency-safe reservation checks)
- Cold chain units against cold_max_units
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import DietType, StorageCondition
from app.core.errors import CapacityExceededException
from app.db.models.capacity import CapacityReservation, CapacityWindow
from app.db.models.recipient import RecipientOrg
from app.schemas.recipient import (
    AcceptsSummary,
    CapacitySnapshot,
    ColdCapacity,
    ProjectionPoint,
)


def ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


@dataclass(frozen=True)
class CapacityWindowSpec:
    start_time: time
    end_time: time
    max_portions: int
    dow: int | None = None
    specific_date: date | None = None


@dataclass(frozen=True)
class ReservationSpec:
    portions: int
    cold_units: int
    state: str  # held | committed | released | consumed
    held_until: datetime | None
    arrives_at: datetime | None


# Pure calculation functions


def is_window_covering(window: CapacityWindowSpec, target_time: datetime) -> bool:
    """Check if a capacity window covers target_time."""
    target_date = target_time.date()
    target_time_of_day = target_time.time()

    if window.specific_date is not None and window.specific_date != target_date:
        return False

    if window.dow is not None and target_time.weekday() != window.dow:
        return False

    # Check time range
    if window.start_time <= window.end_time:
        return window.start_time <= target_time_of_day <= window.end_time
    else:
        # Crosses midnight (e.g. 22:00 to 02:00)
        return target_time_of_day >= window.start_time or target_time_of_day <= window.end_time


def find_matching_window(
    windows: list[CapacityWindowSpec], target_time: datetime
) -> CapacityWindowSpec | None:
    """
    Find the window that covers target_time.
    Specific date takes precedence over day of week.
    """
    date_matches = [
        w
        for w in windows
        if w.specific_date == target_time.date() and is_window_covering(w, target_time)
    ]
    if date_matches:
        return date_matches[0]

    dow_matches = [
        w for w in windows if w.specific_date is None and is_window_covering(w, target_time)
    ]
    if dow_matches:
        return dow_matches[0]

    return None


def compute_projected_stock(
    in_stock_now: float,
    service_rate_per_hour: float,
    now: datetime,
    target_time: datetime,
) -> float:
    """
    projected_stock(t) = max(0, in_stock_now - service_rate_per_hour * hours(t - now))
    """
    if target_time <= now:
        return max(0.0, in_stock_now)

    hours_ahead = (target_time - now).total_seconds() / 3600.0
    served = service_rate_per_hour * hours_ahead
    return max(0.0, in_stock_now - served)


def compute_committed_before(
    reservations: list[ReservationSpec],
    target_time: datetime,
    now: datetime,
) -> int:
    """
    committed_before(t) = Σ portions of held(non-expired) + committed reservations arriving <= t
    """
    total = 0
    for r in reservations:
        if r.state == "held":
            # Only count if not yet expired
            if r.held_until is not None and r.held_until > now:
                # If arrives_at is None, or arrives_at <= target_time
                if r.arrives_at is None or r.arrives_at <= target_time:
                    total += r.portions
        elif r.state == "committed":
            if r.arrives_at is None or r.arrives_at <= target_time:
                total += r.portions
    return total


def compute_cold_used(
    reservations: list[ReservationSpec],
    now: datetime,
) -> int:
    """Sum cold units for all active held and committed reservations."""
    total = 0
    for r in reservations:
        if r.state == "held" and (r.held_until is None or r.held_until > now):
            total += r.cold_units
        elif r.state == "committed":
            total += r.cold_units
    return total


def compute_available_capacity(
    window_max: int | None,
    projected_stock: float,
    committed_before: int,
    is_closed_or_full: bool = False,
    adjustment_delta: int = 0,
) -> int:
    """
    available(t) = max_portions(window containing t) - projected_stock(t) - committed_before(t) + adjustments
    (0 if the org is closed at t or has marked itself full)
    """
    if is_closed_or_full or window_max is None:
        return 0

    effective_max = max(0, window_max + adjustment_delta)
    net_available = effective_max - projected_stock - committed_before
    return max(0, int(net_available))


def project_capacity_timeline(
    windows: list[CapacityWindowSpec],
    in_stock_now: float,
    service_rate_per_hour: float,
    reservations: list[ReservationSpec],
    now: datetime,
    is_closed_or_full: bool = False,
    adjustment_delta: int = 0,
    hours_ahead: float = 6.0,
    step_minutes: int = 15,
) -> list[ProjectionPoint]:
    """Generate 6-hour, 15-minute interval capacity projection points."""
    points: list[ProjectionPoint] = []
    total_steps = int((hours_ahead * 60) / step_minutes)

    for i in range(total_steps + 1):
        step_time = now + timedelta(minutes=i * step_minutes)
        win = find_matching_window(windows, step_time)
        win_max = win.max_portions if win else None

        proj_stock = compute_projected_stock(
            in_stock_now=in_stock_now,
            service_rate_per_hour=service_rate_per_hour,
            now=now,
            target_time=step_time,
        )
        comm = compute_committed_before(reservations, step_time, now)
        avail = compute_available_capacity(
            window_max=win_max,
            projected_stock=proj_stock,
            committed_before=comm,
            is_closed_or_full=is_closed_or_full,
            adjustment_delta=adjustment_delta,
        )
        points.append(ProjectionPoint(at=step_time, available=avail))

    return points


# DB-backed operations


async def get_org_capacity_snapshot(
    session: AsyncSession,
    org_id: uuid.UUID,
    now: datetime,
) -> CapacitySnapshot:
    """Generate full CapacitySnapshot for an organization."""
    query = (
        select(RecipientOrg)
        .where(RecipientOrg.id == org_id)
        .options(
            selectinload(RecipientOrg.capacity_windows),
            selectinload(RecipientOrg.capacity_adjustments),
            selectinload(RecipientOrg.capacity_reservations),
        )
    )
    result = await session.execute(query)
    org = result.scalar_one_or_none()
    if not org:
        raise ValueError(f"Organization {org_id} not found")

    # Convert windows to specs
    window_specs = [
        CapacityWindowSpec(
            start_time=w.start_time,
            end_time=w.end_time,
            max_portions=w.max_portions,
            dow=w.dow,
            specific_date=w.specific_date,
        )
        for w in org.capacity_windows
    ]

    # Convert reservations to specs
    reservation_specs = [
        ReservationSpec(
            portions=r.portions,
            cold_units=r.cold_units,
            state=r.state,
            held_until=ensure_utc(r.held_until),
            arrives_at=ensure_utc(r.arrives_at),
        )
        for r in org.capacity_reservations
        if r.state in ("held", "committed")
    ]

    # Calculate adjustment delta
    adjustment_delta = sum(a.delta_portions for a in org.capacity_adjustments)

    # In-stock portions (delivered and consumed minus served over history, or based on last adjustments)
    consumed_count = sum(r.portions for r in org.capacity_reservations if r.state == "consumed")
    # Estimate in-stock portions
    in_stock_now = max(0, consumed_count + adjustment_delta)

    # Calculate current window
    current_win = find_matching_window(window_specs, now)
    is_open = current_win is not None and org.is_open_override is not False
    max_portions = current_win.max_portions if current_win else 0

    # Calculate held and committed portions
    held_portions = sum(
        r.portions
        for r in reservation_specs
        if r.state == "held" and (r.held_until is None or r.held_until > now)
    )
    committed_portions = sum(r.portions for r in reservation_specs if r.state == "committed")

    # Cold usage
    cold_used = compute_cold_used(reservation_specs, now)

    # Available now
    proj_stock_now = compute_projected_stock(
        in_stock_now=in_stock_now,
        service_rate_per_hour=org.service_rate_per_hour,
        now=now,
        target_time=now,
    )
    available_now = compute_available_capacity(
        window_max=max_portions if is_open else None,
        projected_stock=proj_stock_now,
        committed_before=held_portions + committed_portions,
        is_closed_or_full=not is_open,
        adjustment_delta=adjustment_delta,
    )

    # Projection timeline
    projection = project_capacity_timeline(
        windows=window_specs,
        in_stock_now=in_stock_now,
        service_rate_per_hour=org.service_rate_per_hour,
        reservations=reservation_specs,
        now=now,
        is_closed_or_full=not is_open,
        adjustment_delta=adjustment_delta,
    )

    # Closes at
    closes_at = None
    if current_win:
        end_time_dt = datetime.combine(now.date(), current_win.end_time, tzinfo=now.tzinfo)
        if end_time_dt < now:
            end_time_dt += timedelta(days=1)
        closes_at = end_time_dt

    return CapacitySnapshot(
        org_id=org.id,
        as_of=now,
        max_portions=max_portions,
        in_stock_portions=int(in_stock_now),
        service_rate_per_hour=org.service_rate_per_hour,
        held_portions=held_portions,
        committed_portions=committed_portions,
        cold=ColdCapacity(max=org.cold_max_units, used=cold_used),
        available_now=available_now,
        projection=projection,
        accepts=AcceptsSummary(
            diets=[DietType(d) for d in org.accepts_diets],
            storage=[StorageCondition(s) for s in org.accepts_storage],
        ),
        is_open=is_open,
        closes_at=closes_at,
    )


async def reserve_capacity(
    session: AsyncSession,
    org_id: uuid.UUID,
    portions: int,
    cold_units: int,
    held_until: datetime,
    arrives_at: datetime,
    now: datetime,
    allocation_id: uuid.UUID | None = None,
) -> CapacityReservation:
    """
    Reserve capacity (state='held').
    Concurrency safe: lock org row, check available at arrives_at, create reservation.
    """
    # Select org with FOR UPDATE for concurrency safety
    stmt = select(RecipientOrg).where(RecipientOrg.id == org_id).with_for_update()
    result = await session.execute(stmt)
    org = result.scalar_one_or_none()
    if not org:
        raise ValueError(f"Organization {org_id} not found")

    # Load active reservations
    res_stmt = select(CapacityReservation).where(
        CapacityReservation.org_id == org_id,
        CapacityReservation.state.in_(["held", "committed"]),
    )
    res_result = await session.execute(res_stmt)
    existing_reservations = res_result.scalars().all()

    # Load windows
    win_stmt = select(CapacityWindow).where(CapacityWindow.org_id == org_id)
    win_result = await session.execute(win_stmt)
    windows = win_result.scalars().all()

    window_specs = [
        CapacityWindowSpec(
            start_time=w.start_time,
            end_time=w.end_time,
            max_portions=w.max_portions,
            dow=w.dow,
            specific_date=w.specific_date,
        )
        for w in windows
    ]
    reservation_specs = [
        ReservationSpec(
            portions=r.portions,
            cold_units=r.cold_units,
            state=r.state,
            held_until=ensure_utc(r.held_until),
            arrives_at=ensure_utc(r.arrives_at),
        )
        for r in existing_reservations
    ]

    target_win = find_matching_window(window_specs, arrives_at)
    is_open = target_win is not None and org.is_open_override is not False

    # Check available portions at arrives_at
    proj_stock = compute_projected_stock(
        in_stock_now=0,  # conservative base
        service_rate_per_hour=org.service_rate_per_hour,
        now=now,
        target_time=arrives_at,
    )
    comm_before = compute_committed_before(reservation_specs, arrives_at, now)
    available_at_arrival = compute_available_capacity(
        window_max=target_win.max_portions if is_open else None,
        projected_stock=proj_stock,
        committed_before=comm_before,
        is_closed_or_full=not is_open,
    )

    if portions > available_at_arrival:
        raise CapacityExceededException(
            message=f"{org.name} cannot take {portions} portions (only {available_at_arrival} available at arrival).",
            details={"available": available_at_arrival, "requested": portions},
        )

    # Check cold storage if cold food
    if cold_units > 0:
        cold_used = compute_cold_used(reservation_specs, now)
        if cold_used + cold_units > org.cold_max_units:
            raise CapacityExceededException(
                message=f"{org.name} lacks cold storage ({cold_used}/{org.cold_max_units} units used).",
                details={
                    "cold_max": org.cold_max_units,
                    "cold_used": cold_used,
                    "needed": cold_units,
                },
            )

    reservation = CapacityReservation(
        org_id=org_id,
        allocation_id=allocation_id,
        portions=portions,
        cold_units=cold_units,
        state="held",
        held_until=held_until,
        arrives_at=arrives_at,
    )
    session.add(reservation)
    await session.flush()
    return reservation


async def commit_reservation(
    session: AsyncSession,
    reservation_id: uuid.UUID,
    accepted_portions: int | None = None,
) -> CapacityReservation:
    """Commit a held reservation to 'committed'."""
    stmt = (
        select(CapacityReservation)
        .where(CapacityReservation.id == reservation_id)
        .with_for_update()
    )
    result = await session.execute(stmt)
    reservation = result.scalar_one_or_none()
    if not reservation:
        raise ValueError(f"Reservation {reservation_id} not found")

    if reservation.state != "held":
        raise ValueError(f"Cannot commit reservation in state {reservation.state}")

    if accepted_portions is not None and accepted_portions < reservation.portions:
        reservation.portions = accepted_portions

    reservation.state = "committed"
    reservation.held_until = None
    await session.flush()
    return reservation


async def release_reservation(
    session: AsyncSession,
    reservation_id: uuid.UUID,
) -> CapacityReservation:
    """Release a held or committed reservation to 'released'."""
    stmt = (
        select(CapacityReservation)
        .where(CapacityReservation.id == reservation_id)
        .with_for_update()
    )
    result = await session.execute(stmt)
    reservation = result.scalar_one_or_none()
    if not reservation:
        raise ValueError(f"Reservation {reservation_id} not found")

    reservation.state = "released"
    await session.flush()
    return reservation


async def consume_reservation(
    session: AsyncSession,
    reservation_id: uuid.UUID,
    received_portions: int,
) -> CapacityReservation:
    """Mark reservation as 'consumed' and adjust stock."""
    stmt = (
        select(CapacityReservation)
        .where(CapacityReservation.id == reservation_id)
        .with_for_update()
    )
    result = await session.execute(stmt)
    reservation = result.scalar_one_or_none()
    if not reservation:
        raise ValueError(f"Reservation {reservation_id} not found")

    reservation.state = "consumed"
    reservation.portions = received_portions
    await session.flush()
    return reservation
