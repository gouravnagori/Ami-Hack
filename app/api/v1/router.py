import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.admin import router as admin_router
from app.api.v1.ai import router as ai_router
from app.api.v1.allocations import router as allocations_router
from app.api.v1.auth import router as auth_router
from app.api.v1.donations import router as donations_router
from app.api.v1.driver import (
    _get_driver_by_user,
    _serialize_stop,
    get_current_route_endpoint,
    router as driver_router,
)
from app.api.v1.health import router as health_router
from app.api.v1.impact import router as impact_router
from app.api.v1.offers import router as offers_router
from app.api.v1.org import (
    _get_current_org,
    get_capacity_endpoint,
    router as org_router,
)
from app.api.v1.stops import router as stops_router
from app.api.v1.ws import router as ws_router
from app.core.clock import Clock, get_clock
from app.core.config import Role
from app.core.deps import CurrentUser, require_role
from app.db.session import get_db_session
from app.schemas.recipient import CapacitySnapshot
from app.schemas.route import RouteSchema
from app.services.capacity import get_org_capacity_snapshot
from app.services.dispatch.stops import complete_stop

api_v1_router = APIRouter()

# Mount API routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(donations_router)
api_v1_router.include_router(org_router)
api_v1_router.include_router(offers_router)
api_v1_router.include_router(driver_router)
api_v1_router.include_router(stops_router)
api_v1_router.include_router(allocations_router)
api_v1_router.include_router(impact_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(ws_router)
api_v1_router.include_router(ai_router)


# ── Frontend Route Compatibility Layer ──
class StopDoneCompatRequest(BaseModel):
    otp: str | None = None
    photo_base64: str | None = None
    temp_c: float | None = None


class CapacityUpdateCompatRequest(BaseModel):
    is_open: bool | None = None


@api_v1_router.get(
    "/routes/active",
    response_model=RouteSchema | None,
    tags=["Driver"],
    summary="Get active route (frontend alias)",
)
async def compat_active_route(
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DRIVER))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
):
    return await get_current_route_endpoint(current_user, session, clock)


@api_v1_router.post(
    "/routes/{route_id}/stops/{stop_id}/done",
    tags=["Driver"],
    summary="Complete stop (frontend alias)",
)
async def compat_stop_done(
    route_id: uuid.UUID,
    stop_id: uuid.UUID,
    request: StopDoneCompatRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.DRIVER))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
):
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
    return {"success": True, "stop": _serialize_stop(stop, clock.now())}


@api_v1_router.get(
    "/capacity/current",
    response_model=CapacitySnapshot,
    tags=["Recipient Organization"],
    summary="Current capacity (frontend alias)",
)
async def compat_get_capacity(
    current_user: Annotated[CurrentUser, Depends(require_role(Role.RECIPIENT))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
):
    return await get_capacity_endpoint(current_user, session, clock)


@api_v1_router.post(
    "/capacity",
    response_model=CapacitySnapshot,
    tags=["Recipient Organization"],
    summary="Update capacity (frontend alias)",
)
async def compat_update_capacity(
    request: CapacityUpdateCompatRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(Role.RECIPIENT))],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
):
    org = await _get_current_org(session, current_user.id)
    if request.is_open is not None:
        org.is_open_override = request.is_open
        await session.commit()
    return await get_org_capacity_snapshot(session=session, org_id=org.id, now=clock.now())


