"""
Recipient Organization API router.

Endpoints:
- GET /org/profile: Get organization profile
- PUT /org/profile: Update profile
- GET /org/capacity: Live CapacitySnapshot with 6h projection
- PUT /org/capacity/windows: Configure open windows and capacity
- POST /org/capacity/adjust: Real-time capacity adjustment ledger entry
- POST /org/capacity/full: Toggle manual full override
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.clock import Clock, get_clock
from app.core.config import DietType, Role, StorageCondition
from app.core.deps import CurrentUser, require_role
from app.core.errors import NotFoundException
from app.core.idempotency import Idempotent
from app.db.models.capacity import CapacityAdjustment, CapacityWindow
from app.db.models.recipient import RecipientOrg
from app.db.session import get_db_session
from app.schemas.common import GeoPoint
from app.schemas.recipient import (
    CapacityAdjustRequest,
    CapacityFullRequest,
    CapacitySnapshot,
    CapacityWindowsUpdateRequest,
    IncomingAllocationItem,
    RecipientProfileSchema,
    RecipientProfileUpdate,
)
from app.services.capacity import get_org_capacity_snapshot

router = APIRouter(prefix="/org", tags=["Recipient Organization"])


async def _get_current_org(session: AsyncSession, user_id: uuid.UUID) -> RecipientOrg:
    stmt = (
        select(RecipientOrg)
        .where(RecipientOrg.user_id == user_id)
        .options(
            selectinload(RecipientOrg.capacity_windows),
            selectinload(RecipientOrg.capacity_adjustments),
            selectinload(RecipientOrg.capacity_reservations),
        )
    )
    result = await session.execute(stmt)
    org = result.scalar_one_or_none()
    if not org:
        raise NotFoundException("Recipient organization profile not found for this account")
    return org


@router.get(
    "/profile",
    response_model=RecipientProfileSchema,
    summary="Get recipient organization profile",
)
async def get_profile_endpoint(
    current_user: Annotated[CurrentUser, Depends(require_role(Role.RECIPIENT))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RecipientProfileSchema:
    org = await _get_current_org(session, current_user.id)
    return RecipientProfileSchema(
        id=org.id,
        user_id=org.user_id,
        name=org.name,
        address=org.address,
        geo=GeoPoint(lat=org.lat, lng=org.lng, address=org.address),
        fssai_reg_no=org.fssai_reg_no,
        verified_at=org.verified_at,
        accepts_diets=[DietType(d) for d in org.accepts_diets],
        accepts_storage=[StorageCondition(s) for s in org.accepts_storage],
        cold_max_units=org.cold_max_units,
        service_rate_per_hour=org.service_rate_per_hour,
        need_level=org.need_level,
        is_open_override=org.is_open_override,
        reliability_ewma=org.reliability_ewma,
    )


@router.put(
    "/profile",
    response_model=RecipientProfileSchema,
    summary="Update organization profile",
)
async def update_profile_endpoint(
    request: RecipientProfileUpdate,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.RECIPIENT))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RecipientProfileSchema:
    org = await _get_current_org(session, current_user.id)

    if request.name is not None:
        org.name = request.name
    if request.address is not None:
        org.address = request.address
    if request.lat is not None:
        org.lat = request.lat
    if request.lng is not None:
        org.lng = request.lng
    if request.fssai_reg_no is not None:
        org.fssai_reg_no = request.fssai_reg_no
    if request.accepts_diets is not None:
        org.accepts_diets = [d.value for d in request.accepts_diets]
    if request.accepts_storage is not None:
        org.accepts_storage = [s.value for s in request.accepts_storage]
    if request.cold_max_units is not None:
        org.cold_max_units = request.cold_max_units
    if request.service_rate_per_hour is not None:
        org.service_rate_per_hour = request.service_rate_per_hour
    if request.need_level is not None:
        org.need_level = request.need_level

    await session.commit()

    return RecipientProfileSchema(
        id=org.id,
        user_id=org.user_id,
        name=org.name,
        address=org.address,
        geo=GeoPoint(lat=org.lat, lng=org.lng, address=org.address),
        fssai_reg_no=org.fssai_reg_no,
        verified_at=org.verified_at,
        accepts_diets=[DietType(d) for d in org.accepts_diets],
        accepts_storage=[StorageCondition(s) for s in org.accepts_storage],
        cold_max_units=org.cold_max_units,
        service_rate_per_hour=org.service_rate_per_hour,
        need_level=org.need_level,
        is_open_override=org.is_open_override,
        reliability_ewma=org.reliability_ewma,
    )


@router.get(
    "/capacity",
    response_model=CapacitySnapshot,
    summary="Get live capacity snapshot and 6-hour projection",
)
async def get_capacity_endpoint(
    current_user: Annotated[CurrentUser, Depends(require_role(Role.RECIPIENT))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> CapacitySnapshot:
    org = await _get_current_org(session, current_user.id)
    return await get_org_capacity_snapshot(session=session, org_id=org.id, now=clock.now())


@router.put(
    "/capacity/windows",
    response_model=CapacitySnapshot,
    summary="Update capacity windows",
)
async def update_capacity_windows_endpoint(
    request: CapacityWindowsUpdateRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.RECIPIENT))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> CapacitySnapshot:
    org = await _get_current_org(session, current_user.id)

    # Remove existing windows
    for w in list(org.capacity_windows):
        await session.delete(w)

    for item in request.windows:
        new_win = CapacityWindow(
            org_id=org.id,
            dow=item.dow,
            specific_date=item.specific_date,
            start_time=item.start_time,
            end_time=item.end_time,
            max_portions=item.max_portions,
        )
        session.add(new_win)

    await session.commit()
    return await get_org_capacity_snapshot(session=session, org_id=org.id, now=clock.now())


@router.post(
    "/capacity/adjust",
    response_model=CapacitySnapshot,
    dependencies=[Depends(Idempotent())],
    summary="Append manual capacity adjustment",
)
async def adjust_capacity_endpoint(
    request: CapacityAdjustRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.RECIPIENT))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> CapacitySnapshot:
    org = await _get_current_org(session, current_user.id)

    adjustment = CapacityAdjustment(
        org_id=org.id,
        delta_portions=request.delta_portions,
        reason=request.reason,
        actor_id=current_user.id,
        at=clock.now(),
    )
    session.add(adjustment)
    await session.commit()

    return await get_org_capacity_snapshot(session=session, org_id=org.id, now=clock.now())


@router.post(
    "/capacity/full",
    response_model=CapacitySnapshot,
    summary="Toggle manual full override",
)
async def set_full_override_endpoint(
    request: CapacityFullRequest | None = None,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.RECIPIENT))] = None,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,
    clock: Annotated[Clock, Depends(get_clock)] = None,
) -> CapacitySnapshot:
    org = await _get_current_org(session, current_user.id)
    is_full = True if request is None else request.is_full
    org.is_open_override = False if is_full else True
    await session.commit()

    return await get_org_capacity_snapshot(session=session, org_id=org.id, now=clock.now())


@router.get(
    "/incoming",
    response_model=list[IncomingAllocationItem],
    summary="Allocations en route to this organization with live ETA",
)
async def get_incoming_allocations_endpoint(
    current_user: Annotated[CurrentUser, Depends(require_role(Role.RECIPIENT))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> list[IncomingAllocationItem]:
    from app.core.config import AllocationStatus
    from app.db.models.allocation import Allocation
    from app.db.models.donation import Donation
    from app.db.models.driver import Driver
    from app.services.routing.eta import classify_risk

    org = await _get_current_org(session, current_user.id)
    now = clock.now()

    stmt = (
        select(Allocation)
        .where(
            Allocation.recipient_id == org.id,
            Allocation.status.in_([
                AllocationStatus.DRIVER_ASSIGNED,
                AllocationStatus.PICKED_UP,
            ]),
        )
        .options(
            selectinload(Allocation.donation).selectinload(Donation.items),
            selectinload(Allocation.donation).selectinload(Donation.donor),
            selectinload(Allocation.driver).selectinload(Driver.user),
            selectinload(Allocation.stops),
        )
        .order_by(Allocation.deadline.asc())
    )
    res = await session.execute(stmt)
    allocations = res.scalars().all()

    incoming: list[IncomingAllocationItem] = []
    for a in allocations:
        don = a.donation
        donor_name = don.donor.org_name if (don and don.donor) else "Community Donor"
        item_names = [i.name for i in don.items] if don else []

        driver_id = None
        driver_name = None
        driver_phone = None
        driver_vehicle = None
        if a.driver:
            driver_id = a.driver.id
            driver_name = a.driver.user.name if a.driver.user else "Driver"
            driver_vehicle = a.driver.vehicle_type.value if hasattr(a.driver.vehicle_type, "value") else str(a.driver.vehicle_type)
            if a.driver.user and a.driver.user.phone:
                raw_ph = a.driver.user.phone
                driver_phone = raw_ph[:3] + "****" + raw_ph[-3:] if len(raw_ph) >= 6 else "******"

        pred_delivery = a.predicted_delivery
        dropoff_stop = next((s for s in a.stops if s.type == "dropoff"), None)
        if dropoff_stop and dropoff_stop.predicted_arrival:
            pred_delivery = dropoff_stop.predicted_arrival

        slack = None
        risk_str = "safe"
        if pred_delivery and a.deadline:
            slack = (a.deadline - pred_delivery).total_seconds()
            total_window = (a.deadline - (don.prepared_at if don else now)).total_seconds()
            risk_str = classify_risk(slack, total_window)

        incoming.append(
            IncomingAllocationItem(
                allocation_id=a.id,
                donation_id=a.donation_id,
                portions=a.portions,
                diet=DietType(don.diet) if don else DietType.VEG,
                storage=StorageCondition(don.storage) if don else StorageCondition.AMBIENT,
                status=a.status.value if hasattr(a.status, "value") else str(a.status),
                container_label=a.container_label or "Container A",
                deadline=a.deadline,
                predicted_delivery=pred_delivery,
                slack_seconds=slack,
                risk=risk_str,
                driver_id=driver_id,
                driver_name=driver_name,
                driver_phone=driver_phone,
                driver_vehicle=driver_vehicle,
                donor_name=donor_name,
                items=item_names,
            )
        )

    return incoming

