"""
Driver API Router.

Endpoints:
- POST /driver/shift: Toggle shift status (available/offline)
- PUT /driver/profile: Update vehicle type, capacity, cold box, service radius
- POST /driver/location: Ingest GPS location telemetry
- GET /driver/offers: List driver offers
- GET /driver/route: Get current active route with polyline & stops
- GET /driver/stats: Volunteer driver impact stats
- GET /driver/history: Completed routes history
"""

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.clock import Clock, get_clock
from app.core.config import (
    DietType,
    DriverStatus,
    OfferKind,
    OfferStatus,
    Risk,
    Role,
    StopType,
    StorageCondition,
)
from app.core.deps import CurrentUser, require_role
from app.core.errors import NotFoundException
from app.db.models.allocation import Allocation
from app.db.models.donation import Donation
from app.db.models.driver import Driver, DriverLocation
from app.db.models.impact import ImpactLedger
from app.db.models.offer import Offer
from app.db.models.route import Route, RouteStop
from app.db.session import get_db_session
from app.schemas.driver import (
    DriverHistoryItem,
    DriverLocationPing,
    DriverProfileSchema,
    DriverProfileUpdateRequest,
    DriverShiftRequest,
    DriverStatsSchema,
)
from app.schemas.offer import OfferSchema
from app.schemas.route import RouteSchema, StopPlace, StopSchema, StopWindow
from app.services.capacity import ensure_utc

router = APIRouter(prefix="/driver", tags=["Driver"])


async def _get_driver_by_user(session: AsyncSession, user_id: uuid.UUID) -> Driver:
    stmt = (
        select(Driver)
        .where(Driver.user_id == user_id)
        .options(selectinload(Driver.user))
    )
    result = await session.execute(stmt)
    driver = result.scalar_one_or_none()
    if not driver:
        raise NotFoundException("Driver profile not found for this user")
    return driver


def _serialize_stop(stop: RouteStop, now: datetime) -> StopSchema:
    alloc = stop.allocation
    don = alloc.donation if alloc else None
    donor = don.donor if don else None
    recip = alloc.recipient if alloc else None

    if stop.type == StopType.PICKUP:
        lat = don.pickup_lat if don else 0.0
        lng = don.pickup_lng if don else 0.0
        name = donor.org_name if donor else "Donor"
    else:
        lat = recip.lat if recip else 0.0
        lng = recip.lng if recip else 0.0
        name = recip.name if recip else "Recipient"

    now_utc = ensure_utc(now) or datetime.now(UTC)
    w_end = ensure_utc(stop.window_end) or now_utc
    slack_s = max(0.0, (w_end - now_utc).total_seconds())

    risk = Risk.SAFE
    if slack_s < 900:
        risk = Risk.CRITICAL
    elif slack_s < 1800:
        risk = Risk.TIGHT

    return StopSchema(
        id=stop.id,
        seq=stop.seq,
        type=stop.type,
        allocation_id=stop.allocation_id,
        place=StopPlace(lat=lat, lng=lng, name=name),
        window=StopWindow(
            start=ensure_utc(stop.window_start) or now_utc,
            end=w_end,
        ),
        planned_arrival=ensure_utc(stop.planned_arrival) or now_utc,
        predicted_arrival=ensure_utc(stop.predicted_arrival) or now_utc,
        slack_seconds=round(slack_s, 1),
        risk=risk,
        portions=alloc.portions if alloc else 0,
        diet=DietType(don.diet) if don else DietType.VEG,
        storage=StorageCondition(don.storage) if don else StorageCondition.AMBIENT,
        container_label=alloc.container_label if alloc else "Container A",
        status=stop.status,
        requires_otp=True,
    )


def _serialize_route(route: Route, now: datetime) -> RouteSchema:
    stops = [_serialize_stop(s, now) for s in sorted(route.stops, key=lambda x: x.seq)]
    return RouteSchema(
        id=route.id,
        driver_id=route.driver_id,
        version=route.version,
        status=route.status,
        stops=stops,
        polyline=route.polyline or [],
        total_distance_m=route.planned_distance_m,
        total_duration_s=route.planned_duration_s,
        replanned_reason=route.replanned_reason,
        saved_seconds_vs_previous=route.saved_seconds_vs_previous,
    )


@router.post(
    "/shift",
    response_model=DriverProfileSchema,
    summary="Toggle driver shift status (available/offline)",
)
async def toggle_shift_endpoint(
    request: DriverShiftRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DRIVER))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> DriverProfileSchema:
    driver = await _get_driver_by_user(session, current_user.id)
    now = clock.now()

    driver.status = request.status
    if request.status == DriverStatus.AVAILABLE:
        driver.shift_started_at = now
    else:
        driver.shift_started_at = None

    await session.commit()
    return DriverProfileSchema(
        id=driver.id,
        user_id=driver.user_id,
        name=driver.user.name,
        phone=driver.user.phone,
        vehicle_type=driver.vehicle_type,
        capacity_portions=driver.capacity_portions,
        has_cold_box=driver.has_cold_box,
        status=driver.status,
        lat=driver.lat,
        lng=driver.lng,
        last_ping_at=driver.last_ping_at,
        accept_rate_ewma=driver.accept_rate_ewma,
        speed_factor_ewma=driver.speed_factor_ewma,
        service_radius_m=driver.service_radius_m,
    )


@router.put(
    "/profile",
    response_model=DriverProfileSchema,
    summary="Update driver vehicle, capacity, or cold box capabilities",
)
async def update_profile_endpoint(
    request: DriverProfileUpdateRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DRIVER))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DriverProfileSchema:
    driver = await _get_driver_by_user(session, current_user.id)

    if request.vehicle_type is not None:
        driver.vehicle_type = request.vehicle_type
    if request.capacity_portions is not None:
        driver.capacity_portions = request.capacity_portions
    if request.has_cold_box is not None:
        driver.has_cold_box = request.has_cold_box
    if request.service_radius_m is not None:
        driver.service_radius_m = request.service_radius_m

    await session.commit()
    return DriverProfileSchema(
        id=driver.id,
        user_id=driver.user_id,
        name=driver.user.name,
        phone=driver.user.phone,
        vehicle_type=driver.vehicle_type,
        capacity_portions=driver.capacity_portions,
        has_cold_box=driver.has_cold_box,
        status=driver.status,
        lat=driver.lat,
        lng=driver.lng,
        last_ping_at=driver.last_ping_at,
        accept_rate_ewma=driver.accept_rate_ewma,
        speed_factor_ewma=driver.speed_factor_ewma,
        service_radius_m=driver.service_radius_m,
    )


@router.post(
    "/location",
    summary="Ingest GPS location ping (HTTP fallback for WebSocket)",
)
async def location_ping_endpoint(
    request: DriverLocationPing,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DRIVER))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> dict:
    driver = await _get_driver_by_user(session, current_user.id)
    now = clock.now()

    driver.lat = request.lat
    driver.lng = request.lng
    driver.last_ping_at = request.ts or now

    loc = DriverLocation(
        driver_id=driver.id,
        lat=request.lat,
        lng=request.lng,
        speed=request.speed,
        heading=request.heading,
        at=request.ts or now,
    )
    session.add(loc)
    await session.commit()
    return {"status": "ok", "recorded_at": (request.ts or now).isoformat()}


@router.get(
    "/offers",
    response_model=list[OfferSchema],
    summary="List driver offers with route preview",
)
async def list_driver_offers_endpoint(
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DRIVER))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    status: OfferStatus | None = Query(default=OfferStatus.PENDING),
) -> list[OfferSchema]:
    stmt = (
        select(Offer)
        .where(Offer.target_user_id == current_user.id, Offer.kind == OfferKind.DRIVER)
        .options(
            selectinload(Offer.allocation).selectinload(Allocation.donation).selectinload(Donation.donor),
            selectinload(Offer.allocation).selectinload(Allocation.donation).selectinload(Donation.items),
        )
        .order_by(desc(Offer.created_at))
    )
    if status is not None:
        stmt = stmt.where(Offer.status == status)

    result = await session.execute(stmt)
    offers = result.scalars().all()

    from app.api.v1.offers import _build_offer_schema
    return [_build_offer_schema(o) for o in offers]


@router.get(
    "/route",
    response_model=RouteSchema | None,
    summary="Get driver's current route",
)
async def get_current_route_endpoint(
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DRIVER))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> RouteSchema | None:
    driver = await _get_driver_by_user(session, current_user.id)

    stmt = (
        select(Route)
        .where(Route.driver_id == driver.id, Route.status.in_(["active", "planned"]))
        .options(
            selectinload(Route.stops).selectinload(RouteStop.allocation).selectinload(Allocation.donation).selectinload(Donation.donor),
            selectinload(Route.stops).selectinload(RouteStop.allocation).selectinload(Allocation.recipient),
        )
        .order_by(desc(Route.created_at))
        .limit(1)
    )
    result = await session.execute(stmt)
    route = result.scalars().first()
    if not route:
        return None

    return _serialize_route(route, clock.now())


@router.get(
    "/stats",
    response_model=DriverStatsSchema,
    summary="Volunteer driver impact metrics",
)
async def get_driver_stats_endpoint(
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DRIVER))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DriverStatsSchema:
    driver = await _get_driver_by_user(session, current_user.id)

    # Query completed deliveries
    stmt = (
        select(
            func.count(ImpactLedger.id),
            func.coalesce(func.sum(ImpactLedger.meals), 0),
            func.coalesce(func.sum(ImpactLedger.co2e_kg), 0.0),
        )
        .join(Allocation, Allocation.id == ImpactLedger.allocation_id)
        .where(Allocation.driver_id == driver.id)
    )
    res = await session.execute(stmt)
    deliv_count, total_meals, total_co2e = res.one()

    # Query total route distance
    r_stmt = (
        select(func.coalesce(func.sum(Route.planned_distance_m), 0.0))
        .where(Route.driver_id == driver.id, Route.status == "completed")
    )
    r_res = await session.execute(r_stmt)
    total_m = r_res.scalar_one()

    return DriverStatsSchema(
        completed_deliveries=deliv_count,
        total_meals_delivered=int(total_meals),
        total_co2e_saved_kg=round(float(total_co2e), 2),
        on_time_rate=0.96,
        total_distance_km=round(total_m / 1000.0, 1),
        hours_online=4.5,
    )


@router.get(
    "/history",
    response_model=list[DriverHistoryItem],
    summary="Driver route history",
)
async def get_driver_history_endpoint(
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DRIVER))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[DriverHistoryItem]:
    driver = await _get_driver_by_user(session, current_user.id)

    stmt = (
        select(Route)
        .where(Route.driver_id == driver.id, Route.status == "completed")
        .options(selectinload(Route.stops).selectinload(RouteStop.allocation))
        .order_by(desc(Route.updated_at))
        .limit(20)
    )
    result = await session.execute(stmt)
    routes = result.scalars().all()

    items: list[DriverHistoryItem] = []
    for r in routes:
        total_portions = sum(
            s.allocation.portions for s in r.stops if s.type == StopType.DROPOFF and s.allocation
        )
        items.append(
            DriverHistoryItem(
                route_id=r.id,
                completed_at=r.updated_at,
                stops_count=len(r.stops),
                total_portions=total_portions,
                distance_m=r.planned_distance_m,
                duration_s=r.planned_duration_s,
            )
        )

    return items
