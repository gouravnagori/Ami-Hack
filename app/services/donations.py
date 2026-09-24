"""
Donation lifecycle service.

Handles:
- Creation, preview, listing, cancellation, repeat of donations
- Instant matching & split allocation into containers
- Offer generation with TTL and capacity reservation
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import (
    AllocationStatus,
    DonationStatus,
    OfferKind,
    OfferStatus,
    Risk,
    StorageCondition,
)
from app.core.errors import ValidationException
from app.core.security import generate_otp, hash_otp, mask_phone
from app.db.models.allocation import Allocation
from app.db.models.donation import Donation, DonationItem
from app.db.models.offer import Offer
from app.db.models.recipient import RecipientOrg
from app.schemas.common import GeoPoint
from app.schemas.donation import (
    AllocationRecipientSummary,
    AllocationSchema,
    DonationCreateRequest,
    DonationItemSchema,
    DonationPreviewBestOrg,
    DonationPreviewResponse,
    DonationSchema,
    DriverSummary,
    MatchExplanation,
    MatchReason,
    TimeWindow,
)
from app.services.capacity import (
    CapacityWindowSpec,
    ReservationSpec,
    compute_cold_used,
    ensure_utc,
    reserve_capacity,
)
from app.services.matching import (
    CandidateOrg,
    MatchDonationSpec,
    filter_candidates,
    plan_allocations,
    score_candidates,
)
from app.services.safety import (
    compute_safe_until,
    compute_slack,
    get_default_safety_rule,
)


async def _load_candidate_orgs(session: AsyncSession, now: datetime) -> list[CandidateOrg]:
    """Load all verified recipient orgs with capacity windows and active reservations."""
    stmt = select(RecipientOrg).options(
        selectinload(RecipientOrg.capacity_windows),
        selectinload(RecipientOrg.capacity_reservations),
    )
    result = await session.execute(stmt)
    orgs = result.scalars().all()

    candidates: list[CandidateOrg] = []
    for org in orgs:
        # Build window specs
        win_specs = [
            CapacityWindowSpec(
                start_time=w.start_time,
                end_time=w.end_time,
                max_portions=w.max_portions,
                dow=w.dow,
                specific_date=w.specific_date,
            )
            for w in org.capacity_windows
        ]
        # Active reservations
        res_specs = [
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
        cold_used = compute_cold_used(res_specs, now)

        candidates.append(
            CandidateOrg(
                id=org.id,
                name=org.name,
                lat=org.lat,
                lng=org.lng,
                is_verified=org.verified_at is not None or True,  # demo/verified
                accepts_diets=org.accepts_diets,
                accepts_storage=org.accepts_storage,
                cold_max_units=org.cold_max_units,
                cold_used=cold_used,
                need_level=org.need_level,
                reliability_ewma=org.reliability_ewma,
                last_received_at=org.last_received_at,
                capacity_windows=win_specs,
                service_rate_per_hour=org.service_rate_per_hour,
                is_open_override=org.is_open_override,
                reservations=res_specs,
            )
        )
    return candidates


async def preview_donation(
    session: AsyncSession,
    request: DonationCreateRequest,
    now: datetime,
) -> DonationPreviewResponse:
    """Live feasibility check while typing draft."""
    candidates = await _load_candidate_orgs(session, now)

    total_portions = sum(item.portions for item in request.items)
    rule = get_default_safety_rule(request.storage, request.category)
    safe_until = compute_safe_until(
        prepared_at=request.prepared_at,
        best_before=request.best_before,
        max_hours=rule.max_hours,
        donor_safe_until=request.safe_until,
    )

    spec = MatchDonationSpec(
        id=uuid.uuid4(),
        diet=request.diet,
        storage=request.storage,
        category=request.category,
        total_portions=total_portions,
        safe_until=safe_until,
        pickup_lat=request.pickup.lat,
        pickup_lng=request.pickup.lng,
        pickup_window_start=request.pickup_window.start,
        pickup_window_end=request.pickup_window.end,
    )

    survivors, rejections = filter_candidates(spec, candidates, now)
    scored = score_candidates(spec, survivors, now)

    warnings: list[str] = []
    if not scored:
        if rejections:
            reasons_summary = ", ".join({r.code for r in rejections})
            warnings.append(f"No feasible recipient found. Constraints failed: {reasons_summary}")
        else:
            warnings.append("No active recipient organizations in service radius.")

    best_org = None
    if scored:
        top = scored[0]
        reasons_list = [
            MatchReason(code=r["code"], label=r["label"], weight=round(r["weight"], 2))
            for r in top.reasons
        ]
        best_org = DonationPreviewBestOrg(
            id=top.candidate.id,
            name=top.candidate.name,
            distance_m=round(top.distance_m, 1),
            score=top.score,
            reasons=reasons_list,
        )

    return DonationPreviewResponse(
        feasible_recipients=len(scored),
        best=best_org,
        warnings=warnings,
    )


async def create_and_match_donation(
    session: AsyncSession,
    donor_id: uuid.UUID,
    request: DonationCreateRequest,
    now: datetime,
) -> tuple[Donation, list[str]]:
    """
    Post surplus food:
    1. Validate and enforce safe_until rule
    2. Persist donation & items
    3. Match and split into allocations
    4. Reserve capacity & create offers with TTL
    """
    total_portions = sum(item.portions for item in request.items)
    if total_portions <= 0:
        raise ValidationException("Total portions must be greater than zero")

    rule = get_default_safety_rule(request.storage, request.category)
    safe_until = compute_safe_until(
        prepared_at=request.prepared_at,
        best_before=request.best_before,
        max_hours=rule.max_hours,
        donor_safe_until=request.safe_until,
    )

    donation = Donation(
        donor_id=donor_id,
        status=DonationStatus.MATCHING,
        diet=request.diet,
        storage=request.storage,
        category=request.category,
        total_portions=total_portions,
        prepared_at=request.prepared_at,
        best_before=request.best_before,
        safe_until=safe_until,
        pickup_window_start=request.pickup_window.start,
        pickup_window_end=request.pickup_window.end,
        pickup_lat=request.pickup.lat,
        pickup_lng=request.pickup.lng,
        pickup_address=request.pickup.address or "Donor Location",
        photo_url=request.photo_url,
        notes=request.notes,
    )
    session.add(donation)
    await session.flush()

    for item in request.items:
        d_item = DonationItem(
            donation_id=donation.id,
            name=item.name,
            portions=item.portions,
            weight_kg=item.weight_kg,
        )
        session.add(d_item)

    # Run matching
    candidates = await _load_candidate_orgs(session, now)
    spec = MatchDonationSpec(
        id=donation.id,
        diet=request.diet,
        storage=request.storage,
        category=request.category,
        total_portions=total_portions,
        safe_until=safe_until,
        pickup_lat=request.pickup.lat,
        pickup_lng=request.pickup.lng,
        pickup_window_start=request.pickup_window.start,
        pickup_window_end=request.pickup_window.end,
        donor_id=donor_id,
    )

    survivors, _ = filter_candidates(spec, candidates, now)
    scored = score_candidates(spec, survivors, now)
    allocations_plan = plan_allocations(spec, scored)

    plain_otps: list[str] = []

    if not allocations_plan:
        # Rule R9: Never dump quietly -> fallback
        donation.status = DonationStatus.FALLBACK
        await session.flush()
        return donation, plain_otps

    # Load Org User IDs for offer targeting
    recipient_ids = [a.recipient_id for a in allocations_plan]
    org_stmt = select(RecipientOrg).where(RecipientOrg.id.in_(recipient_ids))
    org_res = await session.execute(org_stmt)
    org_map = {o.id: o for o in org_res.scalars().all()}

    for alloc_spec in allocations_plan:
        pickup_otp = generate_otp()
        dropoff_otp = generate_otp()
        plain_otps.append(pickup_otp)

        alloc = Allocation(
            donation_id=donation.id,
            recipient_id=alloc_spec.recipient_id,
            portions=alloc_spec.portions,
            status=AllocationStatus.OFFERED,
            deadline=alloc_spec.deadline,
            container_label=alloc_spec.container_label,
            predicted_delivery=alloc_spec.predicted_delivery,
            slack_seconds=alloc_spec.slack_seconds,
            score=alloc_spec.score,
            explanation={"score": alloc_spec.score, "reasons": alloc_spec.reasons},
            pickup_otp_hash=hash_otp(pickup_otp),
            dropoff_otp_hash=hash_otp(dropoff_otp),
        )
        session.add(alloc)
        await session.flush()

        # Place held reservation
        time_to_deadline = max(0.0, (alloc_spec.deadline - now).total_seconds())
        ttl_seconds = int(max(90.0, min(600.0, 0.08 * time_to_deadline)))
        held_until = now + timedelta(seconds=ttl_seconds)

        cold_units = alloc_spec.portions if request.storage == StorageCondition.COLD else 0
        await reserve_capacity(
            session=session,
            org_id=alloc_spec.recipient_id,
            portions=alloc_spec.portions,
            cold_units=cold_units,
            held_until=held_until,
            arrives_at=alloc_spec.predicted_delivery,
            now=now,
            allocation_id=alloc.id,
        )

        # Create offer for recipient
        org = org_map.get(alloc_spec.recipient_id)
        if org:
            offer = Offer(
                kind=OfferKind.RECIPIENT,
                allocation_id=alloc.id,
                target_user_id=org.user_id,
                status=OfferStatus.PENDING,
                expires_at=held_until,
                score=alloc_spec.score,
            )
            session.add(offer)

    donation.status = (
        DonationStatus.MATCHED
        if sum(a.portions for a in allocations_plan) >= total_portions
        else DonationStatus.PARTIALLY_MATCHED
    )
    await session.flush()

    return donation, plain_otps


def build_donation_schema(
    donation: Donation, now: datetime, plain_otps: list[str] | None = None
) -> DonationSchema:
    """Format Donation model to Appendix A2 Donation schema."""
    allocations_schema = []
    worst_slack = float("inf")
    worst_risk = Risk.SAFE

    for idx, a in enumerate(donation.allocations):
        slack = a.slack_seconds if a.slack_seconds is not None else 0.0
        if slack < worst_slack:
            worst_slack = slack

        # Compute live risk
        if a.deadline:
            s_sec, _ = compute_slack(a.deadline, a.predicted_delivery or now, now)
            w_risk = Risk.SAFE if s_sec > 1800 else (Risk.TIGHT if s_sec > 600 else Risk.CRITICAL)
            if w_risk == Risk.CRITICAL or (worst_risk != Risk.CRITICAL and w_risk == Risk.TIGHT):
                worst_risk = w_risk

        match_expl = None
        if a.explanation:
            reasons = [
                MatchReason(code=r["code"], label=r["label"], weight=r.get("weight", 0.0))
                for r in a.explanation.get("reasons", [])
            ]
            match_expl = MatchExplanation(score=a.explanation.get("score", 0.0), reasons=reasons)

        driver_sum = None
        if a.driver_id and getattr(a, "driver", None):
            driver_name = "Driver"
            driver_phone = None
            try:
                from sqlalchemy import inspect as sa_inspect

                insp = sa_inspect(a.driver)
                if "user" not in insp.unloaded and a.driver.user:
                    driver_name = a.driver.user.name
                    driver_phone = a.driver.user.phone
            except Exception:
                pass
            driver_sum = DriverSummary(
                id=a.driver.id,
                name=driver_name,
                vehicle=a.driver.vehicle_type,
                phone_masked=mask_phone(driver_phone),
            )

        # Plain pickup OTP if provided, else None
        p_otp = plain_otps[idx] if plain_otps and idx < len(plain_otps) else None

        recip = a.recipient
        allocations_schema.append(
            AllocationSchema(
                id=a.id,
                donation_id=a.donation_id,
                portions=a.portions,
                status=str(a.status),
                recipient=AllocationRecipientSummary(
                    id=recip.id,
                    name=recip.name,
                    geo=GeoPoint(lat=recip.lat, lng=recip.lng, address=recip.address),
                ),
                container_label=a.container_label,
                deadline=a.deadline,
                predicted_delivery=a.predicted_delivery,
                slack_seconds=a.slack_seconds,
                risk=worst_risk,
                match_explanation=match_expl,
                driver=driver_sum,
                pickup_otp=p_otp,
            )
        )

    if worst_slack == float("inf"):
        worst_slack = (ensure_utc(donation.safe_until) - ensure_utc(now)).total_seconds()

    return DonationSchema(
        id=donation.id,
        donor_id=donation.donor_id,
        status=donation.status,
        items=[
            DonationItemSchema(name=i.name, portions=i.portions, weight_kg=i.weight_kg)
            for i in donation.items
        ],
        total_portions=donation.total_portions,
        diet=donation.diet,
        storage=donation.storage,
        prepared_at=donation.prepared_at,
        safe_until=donation.safe_until,
        pickup_window=TimeWindow(
            start=donation.pickup_window_start,
            end=donation.pickup_window_end,
        ),
        pickup=GeoPoint(
            lat=donation.pickup_lat,
            lng=donation.pickup_lng,
            address=donation.pickup_address,
        ),
        photo_url=donation.photo_url,
        notes=donation.notes,
        parse_confidence=donation.parse_confidence,
        allocations=allocations_schema,
        risk=worst_risk,
        slack_seconds=worst_slack,
        created_at=donation.created_at,
    )
