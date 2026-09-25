"""
AI & Agentic Dispatch API — api/v1/ai.py

Endpoints for:
1. Universal Groq-powered AI assistance for all user types (Donor, Shelter, Driver, Ops).
2. Autonomous Agentic Dispatch & Time Negotiation between Donor, Recipient, and Driver.
3. Negotiation history and transcript inspection.
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.clock import Clock, get_clock
from app.core.config import Role
from app.core.deps import CurrentUser, get_current_user
from app.core.errors import NotFoundException
from app.db.models.allocation import Allocation
from app.db.models.donation import Donation
from app.db.session import get_db_session
from app.services.ai.dispatch_agent import dispatch_agent
from app.services.ai.groq_service import groq_service

router = APIRouter(prefix="/ai", tags=["AI & Autonomous Agents"])


class AiAssistRequest(BaseModel):
    query: str = Field(..., min_length=2, description="User question or operational query")
    context: dict[str, Any] | None = Field(default=None, description="Optional page/role context")


class AiAssistResponse(BaseModel):
    reply: str
    role: str
    model: str
    powered_by: str


class AiConfigUpdateRequest(BaseModel):
    api_key: str = Field(..., min_length=8, description="Groq API Key (starts with gsk_)")


class AiStatusResponse(BaseModel):
    groq_configured: bool
    active_model: str
    fast_model: str
    masked_key: str | None = None
    powered_by: str


class AgentNegotiationRequest(BaseModel):
    allocation_id: uuid.UUID | None = None
    donation_id: uuid.UUID | None = None
    donor_name: str | None = None
    donor_address: str | None = None
    recipient_name: str | None = None
    recipient_address: str | None = None
    driver_name: str | None = None
    vehicle_type: str | None = None
    portions: int | None = None
    diet: str | None = None
    storage: str | None = None
    groq_api_key: str | None = None


@router.get(
    "/status",
    response_model=AiStatusResponse,
    summary="Check Groq AI operational status",
)
async def get_ai_status_endpoint() -> AiStatusResponse:
    key = groq_service.get_api_key()
    masked = f"{key[:6]}...{key[-4:]}" if len(key) > 10 else None
    return AiStatusResponse(
        groq_configured=bool(key),
        active_model=groq_service._model,
        fast_model=groq_service._fast_model,
        masked_key=masked,
        powered_by="Groq Llama 3.3" if key else "Algorithmic Solver (Unconfigured)",
    )


@router.post(
    "/config",
    summary="Configure or update Groq API key in runtime and persist to .env",
)
async def update_ai_config_endpoint(
    req: AiConfigUpdateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    key = req.api_key.strip()
    groq_service.set_api_key(key, persist_to_env=True)
    return {
        "success": True,
        "groq_configured": True,
        "message": "Groq API key activated successfully and persisted to .env!",
        "masked_key": f"{key[:6]}...{key[-4:]}" if len(key) > 10 else "configured",
    }


@router.post(
    "/assist",
    response_model=AiAssistResponse,
    summary="Role-tailored AI assistance powered by Groq",
)
async def ai_assist_endpoint(
    req: AiAssistRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AiAssistResponse:
    """
    Provides real-time AI assistance for food safety, tax benefits,
    intake guidelines, cold chain requirements, or operational bottlenecks.
    """
    res = await groq_service.assist(
        role=current_user.role,
        query=req.query,
        user_name=current_user.name,
        context=req.context,
    )
    return AiAssistResponse(
        reply=res["reply"],
        role=res["role"],
        model=res["model"],
        powered_by=res["powered_by"],
    )


@router.post(
    "/agent/negotiate",
    summary="Autonomous multi-agent dispatch negotiation for pickup & delivery timing",
)
async def negotiate_schedule_endpoint(
    req: AgentNegotiationRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    clock: Annotated[Clock, Depends(get_clock)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """
    Autonomous dispatch agent evaluates constraints and conducts negotiation rounds
    between Donor Agent, Driver Agent, and Recipient Agent to agree on a viable
    pickup and delivery window.
    """
    now = clock.now()

    if req.groq_api_key and req.groq_api_key.strip():
        groq_service.set_api_key(req.groq_api_key.strip(), persist_to_env=True)

    donor_info: dict[str, Any] = {
        "name": req.donor_name or "Jaipur Kitchen Partner",
        "address": req.donor_address or "C-Scheme, Jaipur",
        "pickup_window": "Next 45 minutes",
    }
    recipient_info: dict[str, Any] = {
        "name": req.recipient_name or "Asha Shelter Foundation",
        "address": req.recipient_address or "Malviya Nagar, Jaipur",
        "operating_hours": "Open until 19:00",
        "meal_time": "Distribution scheduled in 50 mins",
    }
    driver_info: dict[str, Any] = {
        "name": req.driver_name or "Rescue Driver (E-Rickshaw)",
        "vehicle_type": req.vehicle_type or "e_rickshaw",
        "vehicle_number": "RJ-14-ER-2024",
        "location": "MI Road, Jaipur",
        "eta_to_donor_mins": 14,
        "transit_to_org_mins": 18,
    }
    donation_details: dict[str, Any] = {
        "portions": req.portions or 50,
        "diet": req.diet or "veg",
        "storage": req.storage or "hot",
        "prepared_at": now.isoformat(),
        "safe_until": (now + clock.now().replace(microsecond=0).timetuple()[:0]).isoformat() if False else now.isoformat(),
    }

    # If allocation_id is provided, pull real entities from database
    if req.allocation_id:
        stmt = (
            select(Allocation)
            .where(Allocation.id == req.allocation_id)
            .options(
                selectinload(Allocation.donation).selectinload(Donation.donor),
                selectinload(Allocation.recipient),
                selectinload(Allocation.driver),
            )
        )
        res = (await session.execute(stmt)).scalar_one_or_none()
        if res:
            if res.donation and res.donation.donor:
                donor_info["name"] = res.donation.donor.org_name
                donor_info["address"] = res.donation.donor.pickup_address or res.donation.donor.address
            if res.recipient:
                recipient_info["name"] = res.recipient.name
                recipient_info["address"] = res.recipient.address
            if res.driver:
                driver_info["name"] = f"Driver ({res.driver.vehicle_type})"
                driver_info["vehicle_type"] = res.driver.vehicle_type
            if res.donation:
                donation_details["portions"] = res.donation.total_portions
                donation_details["diet"] = res.donation.diet
                donation_details["storage"] = res.donation.storage

    negotiation = await dispatch_agent.negotiate_schedule(
        donor_info=donor_info,
        recipient_info=recipient_info,
        driver_info=driver_info,
        donation_details=donation_details,
        reference_time=now,
    )

    return negotiation


@router.get(
    "/agent/negotiations/{session_id}",
    summary="Retrieve autonomous agent negotiation details by session ID",
)
async def get_negotiation_session(
    session_id: str,
    _: Annotated[CurrentUser, Depends(get_current_user)],
):
    session_data = dispatch_agent.get_session(session_id)
    if not session_data:
        raise NotFoundException(f"Negotiation session {session_id} not found")
    return session_data
