"""
Allocations API router.

Endpoints:
- POST /allocations/{allocation_id}/confirm-delivery: Recipient confirms receipt of food with OTP
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.clock import Clock, get_clock
from app.core.config import (
    AllocationStatus,
    DonationStatus,
    Role,
    StopStatus,
    StorageCondition,
    settings,
)
from app.core.deps import CurrentUser, require_role
from app.core.errors import AppError, NotFoundException, ValidationException
from app.core.idempotency import Idempotent
from app.core.security import verify_otp
from app.db.models.allocation import Allocation
from app.db.models.donation import Donation
from app.db.models.impact import ImpactLedger
from app.db.models.recipient import RecipientOrg
from app.db.session import get_db_session
from app.schemas.recipient import ConfirmDeliveryRequest, ConfirmDeliveryResponse
from app.services.capacity import consume_reservation
from app.ws.events import emit_allocation_updated

router = APIRouter(prefix="/allocations", tags=["Allocations"])


@router.post(
    "/{allocation_id}/confirm-delivery",
    response_model=ConfirmDeliveryResponse,
    dependencies=[Depends(Idempotent())],
    summary="Confirm delivery of food at recipient organization with OTP",
)
async def confirm_delivery_endpoint(
    allocation_id: uuid.UUID,
    request: ConfirmDeliveryRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.RECIPIENT, Role.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> ConfirmDeliveryResponse:
    now = clock.now()

    # Find recipient org for the user
    stmt_org = select(RecipientOrg).where(RecipientOrg.user_id == current_user.id)
    org = (await session.execute(stmt_org)).scalar_one_or_none()

    # Load allocation
    stmt = (
        select(Allocation)
        .where(Allocation.id == allocation_id)
        .options(
            selectinload(Allocation.donation).selectinload(Donation.allocations),
            selectinload(Allocation.reservations),
            selectinload(Allocation.stops),
        )
    )
    res = await session.execute(stmt)
    alloc = res.scalar_one_or_none()
    if not alloc:
        raise NotFoundException(f"Allocation {allocation_id} not found")

    # Authorize: allocation must belong to recipient org (unless admin)
    if current_user.role != Role.ADMIN:
        if not org or alloc.recipient_id != org.id:
            raise AppError(code="FORBIDDEN", message="Allocation does not belong to your organization")

    # Verify OTP
    if not alloc.dropoff_otp_hash or not verify_otp(request.otp, alloc.dropoff_otp_hash):
        raise ValidationException("Invalid 6-digit delivery OTP")

    # Verify cold chain temperature if cold
    don = alloc.donation
    if don and don.storage == StorageCondition.COLD:
        if request.temp_c is None:
            raise ValidationException("Cold chain drop requires recording temp_c")

    # Mark allocation as delivered
    alloc.status = AllocationStatus.DELIVERED

    # Update dropoff stop if present
    for s in alloc.stops:
        if s.type == "dropoff":
            s.status = StopStatus.DONE
            s.completed_at = now
            if request.temp_c is not None:
                s.temp_c = request.temp_c
            if request.photo_base64:
                s.proof_photo_url = f"proof_{s.id}"

    # Consume capacity reservations
    for r in alloc.reservations:
        if r.state in ("held", "committed"):
            await consume_reservation(session, r.id, received_portions=request.received_portions)

    # Check if impact ledger entry exists
    stmt_imp = select(ImpactLedger).where(ImpactLedger.allocation_id == alloc.id)
    imp_exists = (await session.execute(stmt_imp)).scalar_one_or_none()
    if not imp_exists:
        weight_kg = request.received_portions * settings.PORTION_KG
        co2e_kg = weight_kg * settings.CO2E_PER_KG
        session.add(
            ImpactLedger(
                allocation_id=alloc.id,
                meals=request.received_portions,
                weight_kg=weight_kg,
                co2e_kg=co2e_kg,
                delivered_at=now,
            )
        )

    # If all allocations of donation are delivered, update donation status
    if don and all(a.status == AllocationStatus.DELIVERED for a in don.allocations):
        don.status = DonationStatus.DELIVERED

    await session.commit()

    # Emit WebSocket event
    try:
        await emit_allocation_updated(alloc)
    except Exception:
        pass

    return ConfirmDeliveryResponse(
        status="confirmed",
        allocation_id=alloc.id,
        received_portions=request.received_portions,
        confirmed_at=now,
    )
