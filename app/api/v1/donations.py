"""
Donations API router.

Endpoints:
- POST /donations/preview: Live feasibility check while typing
- POST /donations: Post surplus food (triggers matching & reservation)
- GET /donations: List donor's own donations
- GET /donations/{id}: Detailed donation status and allocations
- POST /donations/{id}/cancel: Cancel active donation
- POST /donations/repeat/{id}: Repeat past donation
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.clock import Clock, get_clock
from app.core.config import DonationStatus, Role
from app.core.deps import CurrentUser, get_current_user, require_role
from app.core.errors import NotFoundException
from app.core.idempotency import Idempotent, get_idempotent_response, save_idempotent_response
from app.db.models.allocation import Allocation
from app.db.models.donation import Donation
from app.db.models.donor import Donor
from app.db.session import get_db_session
from app.schemas.donation import (
    DonationCreateRequest,
    DonationListResponse,
    DonationParseRequest,
    DonationParseResponse,
    DonationPreviewResponse,
    DonationSchema,
)
from app.services.ai.groq_service import groq_service
from app.services.ai.parse import parse_donation_text
from app.services.donations import (
    build_donation_schema,
    create_and_match_donation,
    preview_donation,
)
from app.services.receipts import generate_donation_receipt_pdf

router = APIRouter(prefix="/donations", tags=["Donations"])


@router.post(
    "/preview",
    response_model=DonationPreviewResponse,
    summary="Live feasibility preview while typing",
)
async def preview_donation_endpoint(
    request: DonationCreateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
    _: Annotated[CurrentUser, Depends(require_role(Role.DONOR, Role.ADMIN))],
) -> DonationPreviewResponse:
    return await preview_donation(session=session, request=request, now=clock.now())


@router.post(
    "",
    response_model=DonationSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(Idempotent())],
    summary="Post surplus food",
)
async def create_donation_endpoint(
    request: DonationCreateRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DONOR))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> DonationSchema:
    if idempotency_key:
        cached = await get_idempotent_response(
            db=session,
            key=idempotency_key,
            user_id=str(current_user.id),
            endpoint="/api/v1/donations",
        )
        if cached:
            return DonationSchema.model_validate(cached)

    # Find donor profile
    stmt = select(Donor).where(Donor.user_id == current_user.id)
    result = await session.execute(stmt)
    donor = result.scalar_one_or_none()
    if not donor:
        raise NotFoundException("Donor profile not found for this account")

    now = clock.now()
    donation, plain_otps = await create_and_match_donation(
        session=session,
        donor_id=donor.id,
        request=request,
        now=now,
    )
    await session.commit()

    # Re-fetch with relationships
    fetch_stmt = (
        select(Donation)
        .where(Donation.id == donation.id)
        .options(
            selectinload(Donation.items),
            selectinload(Donation.allocations).selectinload(Allocation.recipient),
            selectinload(Donation.allocations).selectinload(Allocation.driver),
        )
    )
    res = await session.execute(fetch_stmt)
    saved = res.scalar_one()

    schema = build_donation_schema(saved, now=now, plain_otps=plain_otps)
    if idempotency_key:
        await save_idempotent_response(
            db=session,
            key=idempotency_key,
            user_id=str(current_user.id),
            endpoint="/api/v1/donations",
            response_data=schema.model_dump(mode="json"),
        )
        await session.commit()

    # Send donation posted email notification
    try:
        from app.services.notifications.base import notification_service
        await notification_service.notify_donation_posted(
            user_id=str(current_user.id),
            email=current_user.email,
            portions=request.total_portions,
            diet=request.diet,
        )
    except Exception:
        pass  # Don't block donation creation

    return schema


@router.get(
    "",
    response_model=DonationListResponse,
    summary="List donor's own donations",
)
async def list_donations_endpoint(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> DonationListResponse:
    stmt = (
        select(Donation)
        .options(
            selectinload(Donation.items),
            selectinload(Donation.allocations).selectinload(Allocation.recipient),
            selectinload(Donation.allocations).selectinload(Allocation.driver),
        )
        .order_by(desc(Donation.created_at))
        .limit(limit)
    )

    if current_user.role == Role.DONOR:
        donor_stmt = select(Donor).where(Donor.user_id == current_user.id)
        donor_res = await session.execute(donor_stmt)
        donor = donor_res.scalar_one_or_none()
        if not donor:
            return DonationListResponse(items=[])
        stmt = stmt.where(Donation.donor_id == donor.id)

    result = await session.execute(stmt)
    donations = result.scalars().all()
    now = clock.now()

    items = [build_donation_schema(d, now=now) for d in donations]
    return DonationListResponse(items=items)


@router.get(
    "/{donation_id}",
    response_model=DonationSchema,
    summary="Get donation details",
)
async def get_donation_endpoint(
    donation_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> DonationSchema:
    stmt = (
        select(Donation)
        .where(Donation.id == donation_id)
        .options(
            selectinload(Donation.items),
            selectinload(Donation.allocations).selectinload(Allocation.recipient),
            selectinload(Donation.allocations).selectinload(Allocation.driver),
        )
    )
    result = await session.execute(stmt)
    donation = result.scalar_one_or_none()
    if not donation:
        raise NotFoundException(f"Donation {donation_id} not found")

    return build_donation_schema(donation, now=clock.now())


@router.post(
    "/{donation_id}/cancel",
    response_model=DonationSchema,
    summary="Cancel active donation",
)
async def cancel_donation_endpoint(
    donation_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DONOR, Role.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> DonationSchema:
    stmt = (
        select(Donation)
        .where(Donation.id == donation_id)
        .options(
            selectinload(Donation.items),
            selectinload(Donation.allocations).selectinload(Allocation.recipient),
            selectinload(Donation.allocations).selectinload(Allocation.driver),
        )
    )
    result = await session.execute(stmt)
    donation = result.scalar_one_or_none()
    if not donation:
        raise NotFoundException(f"Donation {donation_id} not found")

    donation.status = DonationStatus.CANCELLED
    await session.commit()

    return build_donation_schema(donation, now=clock.now())


@router.post(
    "/parse",
    response_model=DonationParseResponse,
    summary="Parse unstructured donor text into a donation draft",
)
async def parse_donation_endpoint(
    request: DonationParseRequest,
    clock: Annotated[Clock, Depends(get_clock)],
    _: Annotated[CurrentUser, Depends(require_role(Role.DONOR, Role.ADMIN))],
) -> DonationParseResponse:
    res = await groq_service.parse_donation(text=request.text or "", now=clock.now())
    return DonationParseResponse(
        draft=res.get("draft"),
        confidence=float(res.get("confidence", 0.0)),
        missing=res.get("missing", []),
    )


@router.post(
    "/repeat/{donation_id}",
    response_model=DonationSchema,
    status_code=status.HTTP_201_CREATED,
    summary="One-tap repeat of a past donation",
)
async def repeat_donation_endpoint(
    donation_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DONOR))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> DonationSchema:
    from datetime import timedelta

    from app.core.config import DietType, StorageCondition
    from app.schemas.common import GeoPoint
    from app.schemas.donation import DonationItemSchema, TimeWindow

    stmt_donor = select(Donor).where(Donor.user_id == current_user.id)
    donor = (await session.execute(stmt_donor)).scalar_one_or_none()
    if not donor:
        raise NotFoundException("Donor profile not found")

    fetch_stmt = (
        select(Donation)
        .where(Donation.id == donation_id, Donation.donor_id == donor.id)
        .options(selectinload(Donation.items))
    )
    res = await session.execute(fetch_stmt)
    old = res.scalar_one_or_none()
    if not old:
        raise NotFoundException(f"Donation {donation_id} not found")

    now = clock.now()
    window_duration = (old.pickup_window_end - old.pickup_window_start) if (old.pickup_window_end and old.pickup_window_start) else timedelta(hours=2)

    req = DonationCreateRequest(
        items=[DonationItemSchema(name=i.name, portions=i.portions, weight_kg=i.weight_kg) for i in old.items],
        diet=DietType(old.diet),
        storage=StorageCondition(old.storage),
        category=old.category,
        prepared_at=now,
        pickup_window=TimeWindow(start=now, end=now + window_duration),
        pickup=GeoPoint(lat=old.pickup_lat, lng=old.pickup_lng),
        notes=f"Repeat of donation {old.id}",
    )

    new_donation, plain_otps = await create_and_match_donation(
        session=session,
        donor_id=donor.id,
        request=req,
        now=now,
    )
    await session.commit()

    fetch_new = (
        select(Donation)
        .where(Donation.id == new_donation.id)
        .options(
            selectinload(Donation.items),
            selectinload(Donation.allocations).selectinload(Allocation.recipient),
            selectinload(Donation.allocations).selectinload(Allocation.driver),
        )
    )
    saved = (await session.execute(fetch_new)).scalar_one()
    return build_donation_schema(saved, now=now, plain_otps=plain_otps)


@router.get(
    "/{donation_id}/receipt.pdf",
    summary="Download PDF donation receipt & CSR certificate",
)
async def get_donation_receipt_endpoint(
    donation_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    stmt = (
        select(Donation)
        .where(Donation.id == donation_id)
        .options(
            selectinload(Donation.items),
            selectinload(Donation.donor),
            selectinload(Donation.allocations).selectinload(Allocation.recipient),
            selectinload(Donation.allocations).selectinload(Allocation.driver),
        )
    )
    res = await session.execute(stmt)
    donation = res.scalar_one_or_none()
    if not donation:
        raise NotFoundException(f"Donation {donation_id} not found")

    pdf_bytes = generate_donation_receipt_pdf(donation)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=goldenhour_receipt_{donation_id}.pdf"
        },
    )

