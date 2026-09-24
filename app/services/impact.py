"""
Impact and KPI service — services/impact.py (read-only, pure aggregation).

Reads from impact_ledger and allocations/donations to compute:
  - Public landing counters (/impact/public)
  - Per-donor impact (/donor/impact)
  - Per-org impact (/org/impact)
  - KPIs: on_time_rate, median_time_to_match_s
"""

import statistics
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import AllocationStatus, DonationStatus
from app.db.models.allocation import Allocation
from app.db.models.donation import Donation
from app.db.models.donor import Donor
from app.db.models.impact import ImpactLedger
from app.db.models.recipient import RecipientOrg
from app.schemas.impact import ImpactSeriesPoint, ImpactSummary


async def get_public_impact(session: AsyncSession) -> ImpactSummary:
    """Aggregate-level impact counters for the public landing page."""
    totals_stmt = select(
        func.coalesce(func.sum(ImpactLedger.meals), 0),
        func.coalesce(func.sum(ImpactLedger.weight_kg), 0.0),
        func.coalesce(func.sum(ImpactLedger.co2e_kg), 0.0),
    )
    row = (await session.execute(totals_stmt)).one()
    meals_rescued, weight_kg, co2e_kg_avoided = row

    don_count_stmt = select(func.count(Donation.id)).where(
        Donation.status.in_(
            [
                DonationStatus.MATCHED,
                DonationStatus.IN_TRANSIT,
                DonationStatus.DELIVERED,
                DonationStatus.PARTIALLY_MATCHED,
            ]
        )
    )
    donations_total = (await session.execute(don_count_stmt)).scalar_one()
    on_time_rate, median_match_s = await _compute_kpis(session)
    series = await _daily_series(session, days=30)

    return ImpactSummary(
        meals_rescued=int(meals_rescued),
        weight_kg=float(weight_kg),
        co2e_kg_avoided=float(co2e_kg_avoided),
        on_time_rate=on_time_rate,
        median_time_to_match_s=median_match_s,
        donations_total=int(donations_total),
        series=series,
    )


async def get_donor_impact(session: AsyncSession, donor_id: uuid.UUID) -> ImpactSummary:
    """Impact summary for a specific donor."""
    donor_stmt = select(Donor).where(Donor.user_id == donor_id)
    donor_obj = (await session.execute(donor_stmt)).scalar_one_or_none()
    if not donor_obj:
        return _empty_summary()

    don_ids_stmt = select(Donation.id).where(Donation.donor_id == donor_obj.id)
    don_ids = list((await session.execute(don_ids_stmt)).scalars().all())
    if not don_ids:
        return _empty_summary()

    alloc_ids_stmt = select(Allocation.id).where(Allocation.donation_id.in_(don_ids))
    alloc_ids = list((await session.execute(alloc_ids_stmt)).scalars().all())

    if not alloc_ids:
        return _empty_summary()

    totals_stmt = select(
        func.coalesce(func.sum(ImpactLedger.meals), 0),
        func.coalesce(func.sum(ImpactLedger.weight_kg), 0.0),
        func.coalesce(func.sum(ImpactLedger.co2e_kg), 0.0),
    ).where(ImpactLedger.allocation_id.in_(alloc_ids))
    row = (await session.execute(totals_stmt)).one()
    meals_rescued, weight_kg, co2e_kg_avoided = row

    on_time_rate, median_match_s = await _compute_kpis(session, donation_ids=don_ids)
    series = await _daily_series(session, days=30, allocation_ids=alloc_ids)

    return ImpactSummary(
        meals_rescued=int(meals_rescued),
        weight_kg=float(weight_kg),
        co2e_kg_avoided=float(co2e_kg_avoided),
        on_time_rate=on_time_rate,
        median_time_to_match_s=median_match_s,
        donations_total=len(don_ids),
        series=series,
    )


async def get_org_impact(session: AsyncSession, org_id: uuid.UUID) -> ImpactSummary:
    """Impact summary for a specific recipient org."""
    org_stmt = select(RecipientOrg).where(RecipientOrg.user_id == org_id)
    org_obj = (await session.execute(org_stmt)).scalar_one_or_none()
    if not org_obj:
        return _empty_summary()

    alloc_ids_stmt = select(Allocation.id).where(
        Allocation.recipient_id == org_obj.id,
        Allocation.status == AllocationStatus.DELIVERED,
    )
    alloc_ids = list((await session.execute(alloc_ids_stmt)).scalars().all())
    if not alloc_ids:
        return _empty_summary()

    totals_stmt = select(
        func.coalesce(func.sum(ImpactLedger.meals), 0),
        func.coalesce(func.sum(ImpactLedger.weight_kg), 0.0),
        func.coalesce(func.sum(ImpactLedger.co2e_kg), 0.0),
    ).where(ImpactLedger.allocation_id.in_(alloc_ids))
    row = (await session.execute(totals_stmt)).one()
    meals_rescued, weight_kg, co2e_kg_avoided = row

    on_time_rate, median_match_s = await _compute_kpis(session, allocation_ids=alloc_ids)
    series = await _daily_series(session, days=30, allocation_ids=alloc_ids)

    return ImpactSummary(
        meals_rescued=int(meals_rescued),
        weight_kg=float(weight_kg),
        co2e_kg_avoided=float(co2e_kg_avoided),
        on_time_rate=on_time_rate,
        median_time_to_match_s=median_match_s,
        donations_total=len(alloc_ids),
        series=series,
    )


async def _compute_kpis(
    session: AsyncSession,
    donation_ids: list[uuid.UUID] | None = None,
    allocation_ids: list[uuid.UUID] | None = None,
) -> tuple[float, float]:
    from app.services.capacity import ensure_utc

    alloc_stmt = (
        select(Allocation)
        .options(selectinload(Allocation.donation))
        .where(Allocation.status == AllocationStatus.DELIVERED)
    )
    if allocation_ids is not None:
        alloc_stmt = alloc_stmt.where(Allocation.id.in_(allocation_ids))
    elif donation_ids is not None:
        alloc_stmt = alloc_stmt.where(Allocation.donation_id.in_(donation_ids))

    allocs = (await session.execute(alloc_stmt)).scalars().all()
    on_time_count = 0
    total_count = len(allocs)
    match_times_s: list[float] = []

    for a in allocs:
        if a.predicted_delivery and a.deadline:
            pd = ensure_utc(a.predicted_delivery)
            dl = ensure_utc(a.deadline)
            if pd and dl and pd <= dl:
                on_time_count += 1
        else:
            on_time_count += 1

        if a.donation and a.donation.created_at and a.created_at:
            delta = (a.created_at - a.donation.created_at).total_seconds()
            if delta >= 0:
                match_times_s.append(delta)

    on_time_rate = (on_time_count / total_count) if total_count > 0 else 1.0
    median_match_s = statistics.median(match_times_s) if match_times_s else 0.0
    return round(on_time_rate, 4), round(median_match_s, 2)


async def _daily_series(
    session: AsyncSession,
    days: int = 30,
    allocation_ids: list[uuid.UUID] | None = None,
) -> list[ImpactSeriesPoint]:
    from app.services.capacity import ensure_utc

    cutoff = datetime.now(UTC) - timedelta(days=days)
    stmt = select(ImpactLedger.delivered_at, ImpactLedger.meals).where(
        ImpactLedger.delivered_at >= cutoff
    )
    if allocation_ids is not None:
        stmt = stmt.where(ImpactLedger.allocation_id.in_(allocation_ids))

    rows = (await session.execute(stmt)).all()
    daily: dict[str, int] = {}
    for delivered_at, meals in rows:
        dt = ensure_utc(delivered_at)
        if dt:
            date_str = dt.date().isoformat()
            daily[date_str] = daily.get(date_str, 0) + int(meals)

    return [ImpactSeriesPoint(date=d, meals=m) for d, m in sorted(daily.items())]


def _empty_summary() -> ImpactSummary:
    return ImpactSummary(
        meals_rescued=0,
        weight_kg=0.0,
        co2e_kg_avoided=0.0,
        on_time_rate=1.0,
        median_time_to_match_s=0.0,
        donations_total=0,
        series=[],
    )
