"""
Offers API router.

Endpoints:
- GET /offers: List offers for current recipient/driver
- POST /offers/{id}/accept: Accept offer (commits reservation, supports partial portion acceptance)
- POST /offers/{id}/decline: Decline offer (releases reservation, triggers cascade)
"""

import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.clock import Clock, get_clock
from app.core.config import (
    AllocationStatus,
    DriverStatus,
    OfferKind,
    OfferStatus,
    StopStatus,
    StopType,
)
from app.core.deps import CurrentUser, get_current_user
from app.core.errors import AppError, NotFoundException
from app.core.idempotency import Idempotent
from app.db.models.allocation import Allocation
from app.db.models.donation import Donation
from app.db.models.driver import Driver
from app.db.models.offer import Offer
from app.db.models.route import Route, RouteStop
from app.db.session import get_db_session
from app.schemas.donation import MatchExplanation, MatchReason
from app.schemas.offer import (
    OfferAcceptRequest,
    OfferDeclineRequest,
    OfferDonationSummary,
    OfferSchema,
)
from app.services.capacity import commit_reservation, ensure_utc, release_reservation
from app.services.dispatch.engine import dispatch_pending_tasks
from app.services.matching import haversine_distance_m

router = APIRouter(prefix="/offers", tags=["Offers"])


def _build_offer_schema(
    offer: Offer, user_lat: float = 28.6139, user_lng: float = 77.2090
) -> OfferSchema:
    alloc = offer.allocation
    donation = alloc.donation if alloc else None

    # Distance calculation
    dist = 1200.0
    if donation:
        dist = haversine_distance_m(donation.pickup_lat, donation.pickup_lng, user_lat, user_lng)

    donor_name = (
        donation.donor.org_name
        if donation and getattr(donation, "donor", None)
        else "Surplus Donor"
    )
    items_list = (
        [i.name for i in donation.items] if donation and getattr(donation, "items", None) else []
    )

    donation_summary = OfferDonationSummary(
        id=donation.id if donation else uuid.uuid4(),
        donor_name=donor_name,
        diet=donation.diet if donation else alloc.donation.diet,
        storage=donation.storage if donation else alloc.donation.storage,
        total_portions=donation.total_portions if donation else (alloc.portions if alloc else 0),
        safe_until=donation.safe_until if donation else alloc.deadline,
        distance_m=round(dist, 1),
        items=items_list,
    )

    match_expl = None
    if alloc and alloc.explanation:
        reasons = [
            MatchReason(code=r["code"], label=r["label"], weight=r.get("weight", 0.0))
            for r in alloc.explanation.get("reasons", [])
        ]
        match_expl = MatchExplanation(score=alloc.explanation.get("score", 0.0), reasons=reasons)

    return OfferSchema(
        id=offer.id,
        kind=offer.kind,
        status=offer.status,
        created_at=offer.created_at,
        expires_at=offer.expires_at,
        donation=donation_summary,
        max_acceptable_portions=alloc.portions if alloc else None,
        offered_portions=alloc.portions if alloc else None,
        match_explanation=match_expl,
        route_preview=offer.route_preview,
    )


@router.get(
    "",
    response_model=list[OfferSchema],
    summary="List offers for current user",
)
async def list_offers_endpoint(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    status: OfferStatus | None = Query(default=OfferStatus.PENDING),
) -> list[OfferSchema]:
    stmt = (
        select(Offer)
        .where(Offer.target_user_id == current_user.id)
        .options(
            selectinload(Offer.allocation)
            .selectinload(Allocation.donation)
            .selectinload(Donation.donor),
            selectinload(Offer.allocation)
            .selectinload(Allocation.donation)
            .selectinload(Donation.items),
        )
        .order_by(desc(Offer.created_at))
    )

    if status is not None:
        stmt = stmt.where(Offer.status == status)

    result = await session.execute(stmt)
    offers = result.scalars().all()

    return [_build_offer_schema(o) for o in offers]


@router.post(
    "/{offer_id}/accept",
    response_model=OfferSchema,
    dependencies=[Depends(Idempotent())],
    summary="Accept an offer (commits reservation)",
)
async def accept_offer_endpoint(
    offer_id: uuid.UUID,
    request: OfferAcceptRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> OfferSchema:
    stmt = (
        select(Offer)
        .where(Offer.id == offer_id, Offer.target_user_id == current_user.id)
        .options(
            selectinload(Offer.allocation)
            .selectinload(Allocation.donation)
            .selectinload(Donation.donor),
            selectinload(Offer.allocation)
            .selectinload(Allocation.donation)
            .selectinload(Donation.items),
            selectinload(Offer.allocation).selectinload(Allocation.reservations),
        )
        .with_for_update()
    )
    result = await session.execute(stmt)
    offer = result.scalar_one_or_none()
    if not offer:
        raise NotFoundException(f"Offer {offer_id} not found")

    now = clock.now()
    if offer.status != OfferStatus.PENDING:
        raise AppError(code="OFFER_NOT_PENDING", message=f"Offer is already {offer.status}")

    if ensure_utc(offer.expires_at) < ensure_utc(now):
        offer.status = OfferStatus.EXPIRED
        await session.commit()
        raise AppError(code="OFFER_EXPIRED", message="This offer has expired")

    alloc = offer.allocation
    if alloc:
        if offer.kind == OfferKind.DRIVER:
            # Driver accepts route assignment
            driver_stmt = select(Driver).where(Driver.user_id == current_user.id)
            d_res = await session.execute(driver_stmt)
            driver = d_res.scalar_one_or_none()
            if driver:
                driver.status = DriverStatus.ON_TASK
                alloc.driver_id = driver.id
                alloc.status = AllocationStatus.DRIVER_ASSIGNED

                # Create Route and Stops from preview
                preview = offer.route_preview or {}
                route = Route(
                    driver_id=driver.id,
                    version=1,
                    status="active",
                    planned_distance_m=preview.get("total_distance_m", 0.0),
                    planned_duration_s=preview.get("total_duration_s", 0.0),
                    polyline=preview.get("polyline", []),
                    replanned_reason=preview.get("replanned_reason"),
                    saved_seconds_vs_previous=preview.get("saved_seconds_vs_previous"),
                )
                session.add(route)
                await session.flush()

                # Add stops
                don = alloc.donation
                pickup_stop = RouteStop(
                    route_id=route.id,
                    seq=1,
                    type=StopType.PICKUP,
                    allocation_id=alloc.id,
                    planned_arrival=now,
                    predicted_arrival=now,
                    window_start=don.pickup_window_start if don else now,
                    window_end=don.pickup_window_end if don else (now + timedelta(hours=2)),
                    slack_seconds=alloc.slack_seconds or 0.0,
                    status=StopStatus.PENDING,
                )
                session.add(pickup_stop)

                dropoff_stop = RouteStop(
                    route_id=route.id,
                    seq=2,
                    type=StopType.DROPOFF,
                    allocation_id=alloc.id,
                    planned_arrival=alloc.predicted_delivery or (now + timedelta(minutes=30)),
                    predicted_arrival=alloc.predicted_delivery or (now + timedelta(minutes=30)),
                    window_start=don.pickup_window_start if don else now,
                    window_end=alloc.deadline,
                    slack_seconds=alloc.slack_seconds or 0.0,
                    status=StopStatus.PENDING,
                )
                session.add(dropoff_stop)

        else:
            # Recipient accepts portion allocation
            accepted_portions = request.portions or alloc.portions
            alloc.status = AllocationStatus.ACCEPTED
            alloc.portions = accepted_portions

            for res in alloc.reservations:
                if res.state == "held":
                    await commit_reservation(session, res.id, accepted_portions=accepted_portions)

            # Withdraw any parallel competing recipient offers for the same allocation
            competing_stmt = select(Offer).where(
                Offer.allocation_id == alloc.id,
                Offer.id != offer.id,
                Offer.kind == OfferKind.RECIPIENT,
                Offer.status == OfferStatus.PENDING,
            )
            comp_res = await session.execute(competing_stmt)
            for comp_offer in comp_res.scalars().all():
                comp_offer.status = OfferStatus.WITHDRAWN

            # Trigger driver dispatch for this accepted allocation
            await dispatch_pending_tasks(session, now)

    offer.status = OfferStatus.ACCEPTED
    offer.responded_at = now
    await session.commit()

    return _build_offer_schema(offer)


@router.post(
    "/{offer_id}/decline",
    response_model=OfferSchema,
    summary="Decline an offer (releases reservation)",
)
async def decline_offer_endpoint(
    offer_id: uuid.UUID,
    request: OfferDeclineRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> OfferSchema:
    stmt = (
        select(Offer)
        .where(Offer.id == offer_id, Offer.target_user_id == current_user.id)
        .options(
            selectinload(Offer.allocation)
            .selectinload(Allocation.donation)
            .selectinload(Donation.donor),
            selectinload(Offer.allocation)
            .selectinload(Allocation.donation)
            .selectinload(Donation.items),
            selectinload(Offer.allocation).selectinload(Allocation.reservations),
        )
        .with_for_update()
    )
    result = await session.execute(stmt)
    offer = result.scalar_one_or_none()
    if not offer:
        raise NotFoundException(f"Offer {offer_id} not found")

    now = clock.now()
    if offer.status != OfferStatus.PENDING:
        raise AppError(code="OFFER_NOT_PENDING", message=f"Offer is already {offer.status}")

    # Release held reservation
    alloc = offer.allocation
    if alloc:
        for res in alloc.reservations:
            if res.state == "held":
                await release_reservation(session, res.id)

    offer.status = OfferStatus.DECLINED
    offer.responded_at = now
    await session.commit()

    return _build_offer_schema(offer)
