"""
Stops API Router.

Endpoints:
- POST /stops/{id}/arrive: Driver arrives at pickup/dropoff stop
- POST /stops/{id}/complete: Verify OTP, record cold temp_c, complete stop & settle impact
- POST /stops/{id}/issue: Report issue (food_not_ready, recipient_closed, vehicle_issue, unsafe_food, other)
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.driver import _get_driver_by_user, _serialize_stop
from app.core.clock import Clock, get_clock
from app.core.config import Role
from app.core.deps import CurrentUser, require_role
from app.core.idempotency import Idempotent
from app.db.session import get_db_session
from app.schemas.route import StopCompleteRequest, StopIssueRequest, StopSchema
from app.services.dispatch.stops import arrive_stop, complete_stop, report_stop_issue

router = APIRouter(prefix="/stops", tags=["Stops"])


@router.post(
    "/{stop_id}/arrive",
    response_model=StopSchema,
    summary="Record driver arrival at a stop",
)
async def arrive_stop_endpoint(
    stop_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DRIVER))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> StopSchema:
    driver = await _get_driver_by_user(session, current_user.id)
    stop = await arrive_stop(session, stop_id, driver.id, clock.now())
    return _serialize_stop(stop, clock.now())


@router.post(
    "/{stop_id}/complete",
    response_model=StopSchema,
    dependencies=[Depends(Idempotent())],
    summary="Complete stop with OTP verification and cold-chain temperature check",
)
async def complete_stop_endpoint(
    stop_id: uuid.UUID,
    request: StopCompleteRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DRIVER))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> StopSchema:
    driver = await _get_driver_by_user(session, current_user.id)
    stop = await complete_stop(
        session=session,
        stop_id=stop_id,
        driver_id=driver.id,
        otp=request.otp,
        photo_base64=request.photo_base64,
        temp_c=request.temp_c,
        now=clock.now(),
    )
    return _serialize_stop(stop, clock.now())


@router.post(
    "/{stop_id}/issue",
    response_model=StopSchema,
    summary="Report operational issue on a stop",
)
async def report_issue_endpoint(
    stop_id: uuid.UUID,
    request: StopIssueRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DRIVER))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> StopSchema:
    driver = await _get_driver_by_user(session, current_user.id)
    stop = await report_stop_issue(
        session=session,
        stop_id=stop_id,
        driver_id=driver.id,
        code=request.code,
        note=request.note,
        now=clock.now(),
    )
    return _serialize_stop(stop, clock.now())
