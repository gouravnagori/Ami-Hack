"""
Recipient matching engine — pure decision core.

Steps:
1. Hard filters (with explicit rejection reason codes)
2. Normalized scoring [0, 100] with top 3 human-readable reasons
3. Split allocation (Wedding-Night mode) for large donations across shelters
4. Cascade planning (ttl calculation, parallel offers for tight deadlines)
"""

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.core.config import DietType, Risk, StorageCondition
from app.services.capacity import (
    CapacityWindowSpec,
    ReservationSpec,
    compute_available_capacity,
    compute_committed_before,
    compute_projected_stock,
    find_matching_window,
)
from app.services.safety import (
    classify_risk,
    compute_deadline,
    compute_predicted_delivery,
    compute_slack,
    get_default_safety_rule,
    is_feasible,
)


@dataclass(frozen=True)
class CandidateOrg:
    id: uuid.UUID
    name: str
    lat: float
    lng: float
    is_verified: bool
    accepts_diets: list[DietType]
    accepts_storage: list[StorageCondition]
    cold_max_units: int
    cold_used: int
    need_level: float  # 0.0 to 1.0
    reliability_ewma: float  # 0.0 to 1.0
    last_received_at: datetime | None
    capacity_windows: list[CapacityWindowSpec]
    service_rate_per_hour: float = 20.0
    is_open_override: bool | None = None
    preferred_donors: set[uuid.UUID] = field(default_factory=set)
    reservations: list[ReservationSpec] = field(default_factory=list)


@dataclass(frozen=True)
class MatchDonationSpec:
    id: uuid.UUID
    diet: DietType
    storage: StorageCondition
    category: str
    total_portions: int
    safe_until: datetime
    pickup_lat: float
    pickup_lng: float
    pickup_window_start: datetime
    pickup_window_end: datetime
    donor_id: uuid.UUID | None = None
    blocked_org_ids: set[uuid.UUID] = field(default_factory=set)


@dataclass(frozen=True)
class FilterRejection:
    org_id: uuid.UUID
    org_name: str
    code: str
    message: str


@dataclass(frozen=True)
class ScoredCandidate:
    candidate: CandidateOrg
    score: float
    available_portions: int
    predicted_delivery: datetime
    deadline: datetime
    slack_seconds: float
    slack_ratio: float
    risk: Risk
    distance_m: float
    sub_scores: dict[str, float]
    reasons: list[dict[str, Any]]


@dataclass(frozen=True)
class SplitAllocation:
    recipient_id: uuid.UUID
    recipient_name: str
    recipient_lat: float
    recipient_lng: float
    portions: int
    container_label: str
    deadline: datetime
    predicted_delivery: datetime
    slack_seconds: float
    risk: Risk
    score: float
    reasons: list[dict[str, Any]]


@dataclass(frozen=True)
class CascadeOfferPlan:
    allocation_id: uuid.UUID | None
    recipient_id: uuid.UUID
    recipient_name: str
    portions: int
    ttl_seconds: int
    is_parallel: bool
    score: float


# Helper functions


def haversine_distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the great-circle distance between two points in metres."""
    r = 6371000.0  # Earth's radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def estimate_transit_seconds(distance_m: float, avg_speed_kmh: float = 22.0) -> float:
    """Estimate transit time with 1.35 urban detour factor."""
    detour_distance = distance_m * 1.35
    speed_mps = (avg_speed_kmh * 1000.0) / 3600.0
    return detour_distance / max(speed_mps, 1.0)


# Step 1: Hard Filters


def filter_candidates(
    donation: MatchDonationSpec,
    candidates: list[CandidateOrg],
    now: datetime,
    max_radius_m: float = 25000.0,
) -> tuple[
    list[tuple[CandidateOrg, int, datetime, datetime, float, float, Risk, float]],
    list[FilterRejection],
]:
    """
    Apply hard filters. Returns:
    - survivors: list of (candidate, available_portions, predicted_delivery, deadline, slack_seconds, slack_ratio, risk, distance_m)
    - rejections: list of FilterRejection
    """
    survivors = []
    rejections: list[FilterRejection] = []

    rule = get_default_safety_rule(donation.storage, donation.category)
    min_chunk = max(10, int(0.20 * donation.total_portions))

    for org in candidates:
        # 1. Block list
        if org.id in donation.blocked_org_ids:
            rejections.append(
                FilterRejection(org.id, org.name, "BLOCKED", f"{org.name} is on donor block list")
            )
            continue

        # 2. Verification / active check
        if not org.is_verified:
            rejections.append(
                FilterRejection(org.id, org.name, "NOT_VERIFIED", f"{org.name} is not verified")
            )
            continue

        # 3. Dietary constraint (R2)
        if donation.diet not in org.accepts_diets:
            rejections.append(
                FilterRejection(
                    org.id,
                    org.name,
                    "DIET_MISMATCH",
                    f"{org.name} does not accept {donation.diet} food",
                )
            )
            continue

        # 4. Storage condition & cold chain (R3)
        if donation.storage not in org.accepts_storage:
            rejections.append(
                FilterRejection(
                    org.id,
                    org.name,
                    "COLD_CHAIN_UNAVAILABLE",
                    f"{org.name} does not accept {donation.storage} food",
                )
            )
            continue

        if donation.storage == StorageCondition.COLD:
            free_cold = org.cold_max_units - org.cold_used
            if free_cold < 1:
                rejections.append(
                    FilterRejection(
                        org.id,
                        org.name,
                        "COLD_CHAIN_UNAVAILABLE",
                        f"{org.name} has no available cold storage units",
                    )
                )
                continue

        # 5. Distance check
        dist_m = haversine_distance_m(donation.pickup_lat, donation.pickup_lng, org.lat, org.lng)
        if dist_m > max_radius_m:
            rejections.append(
                FilterRejection(
                    org.id,
                    org.name,
                    "DISTANCE_EXCEEDED",
                    f"{org.name} is {dist_m / 1000:.1f}km away (limit {max_radius_m / 1000:.1f}km)",
                )
            )
            continue

        # 6. Time feasibility (R4)
        transit_sec = estimate_transit_seconds(dist_m)
        predicted_delivery = compute_predicted_delivery(
            now=now,
            eta_to_pickup_seconds=600.0,  # 10 min driver to pickup estimate
            eta_pickup_to_dropoff_seconds=transit_sec,
        )

        win = find_matching_window(org.capacity_windows, predicted_delivery)
        if win is None or org.is_open_override is False:
            rejections.append(
                FilterRejection(
                    org.id, org.name, "CLOSED_AT_ETA", f"{org.name} is closed at predicted ETA"
                )
            )
            continue

        # Compute deadline and slack
        win_end_dt = datetime.combine(
            predicted_delivery.date(), win.end_time, tzinfo=predicted_delivery.tzinfo
        )
        if win_end_dt < predicted_delivery:
            win_end_dt += timedelta(days=1)

        deadline = compute_deadline(
            safe_until=donation.safe_until,
            recipient_window_end=win_end_dt,
            handling_buffer_minutes=rule.handling_buffer_minutes,
        )

        if not is_feasible(
            predicted_delivery=predicted_delivery,
            deadline=deadline,
            transit_duration_seconds=transit_sec,
            transit_cap_minutes=rule.transit_cap_minutes,
        ):
            rejections.append(
                FilterRejection(
                    org.id,
                    org.name,
                    "WINDOW_INFEASIBLE",
                    f"{org.name} cannot receive food before expiry deadline",
                )
            )
            continue

        slack_sec, slack_ratio = compute_slack(deadline, predicted_delivery, now)
        risk = classify_risk(slack_sec, (deadline - now).total_seconds())

        # 7. Available capacity (R1)
        proj_stock = compute_projected_stock(
            in_stock_now=0,
            service_rate_per_hour=org.service_rate_per_hour,
            now=now,
            target_time=predicted_delivery,
        )
        comm_before = compute_committed_before(org.reservations, predicted_delivery, now)
        avail = compute_available_capacity(
            window_max=win.max_portions,
            projected_stock=proj_stock,
            committed_before=comm_before,
            is_closed_or_full=False,
        )

        if avail < min_chunk:
            rejections.append(
                FilterRejection(
                    org.id,
                    org.name,
                    "BELOW_MIN_CHUNK",
                    f"{org.name} has only {avail} capacity (min chunk is {min_chunk})",
                )
            )
            continue

        survivors.append(
            (org, avail, predicted_delivery, deadline, slack_sec, slack_ratio, risk, dist_m)
        )

    return survivors, rejections


# Step 2: Scoring Engine


def score_candidates(
    donation: MatchDonationSpec,
    survivors: list[tuple[CandidateOrg, int, datetime, datetime, float, float, Risk, float]],
    now: datetime,
    max_radius_m: float = 25000.0,
) -> list[ScoredCandidate]:
    """
    Score survivors [0, 100] using weighted formula:
    time (0.28) + distance (0.18) + fit (0.14) + need (0.14) +
    reliability (0.10) + fairness (0.08) + preference (0.08)
    """
    scored = []

    for org, avail, pred_del, deadline, slack_sec, slack_ratio, risk, dist_m in survivors:
        # 1. Time score (slack ratio clipped [0, 1])
        s_time = max(0.0, min(1.0, slack_ratio))

        # 2. Distance score (1 - d/d_max)
        s_distance = max(0.0, 1.0 - (dist_m / max_radius_m))

        # 3. Fit score: reward <= 0.85, penalise near-full
        ratio = donation.total_portions / max(1, avail)
        if ratio <= 0.85:
            s_fit = min(1.0, ratio / 0.85)
        else:
            s_fit = max(0.2, 1.0 - (ratio - 0.85) * 2.0)

        # 4. Need score
        s_need = max(0.0, min(1.0, org.need_level))

        # 5. Reliability score
        s_reliability = max(0.0, min(1.0, org.reliability_ewma))

        # 6. Fairness: log-scaled time since last received food
        if org.last_received_at is None:
            s_fairness = 1.0
        else:
            hours_since = max(0.0, (now - org.last_received_at).total_seconds() / 3600.0)
            s_fairness = min(1.0, math.log1p(hours_since) / math.log1p(72.0))

        # 7. Preference score
        s_pref = 0.5
        if donation.donor_id and donation.donor_id in org.preferred_donors:
            s_pref = 1.0

        # Weighted sum
        weights = {
            "time": 0.28,
            "distance": 0.18,
            "fit": 0.14,
            "need": 0.14,
            "reliability": 0.10,
            "fairness": 0.08,
            "preference": 0.08,
        }
        sub_scores = {
            "time": s_time,
            "distance": s_distance,
            "fit": s_fit,
            "need": s_need,
            "reliability": s_reliability,
            "fairness": s_fairness,
            "preference": s_pref,
        }

        total_score = 100.0 * sum(weights[k] * sub_scores[k] for k in weights)

        # Top 3 human reasons
        reasons_candidates = [
            {
                "code": "TIME_SLACK",
                "label": f"{int(slack_sec // 60)} min to spare before expiry",
                "weight": weights["time"] * s_time,
            },
            {
                "code": "HIGH_NEED",
                "label": f"Urgent need level ({int(org.need_level * 100)}%)",
                "weight": weights["need"] * s_need,
            },
            {
                "code": "PROXIMITY",
                "label": f"Only {dist_m / 1000.0:.1f} km away",
                "weight": weights["distance"] * s_distance,
            },
            {
                "code": "CAPACITY_FIT",
                "label": f"Has room for {avail} portions",
                "weight": weights["fit"] * s_fit,
            },
            {
                "code": "RELIABILITY",
                "label": f"High completion rate ({int(org.reliability_ewma * 100)}%)",
                "weight": weights["reliability"] * s_reliability,
            },
        ]
        reasons_candidates.sort(key=lambda r: r["weight"], reverse=True)
        top_reasons = reasons_candidates[:3]

        scored.append(
            ScoredCandidate(
                candidate=org,
                score=round(total_score, 1),
                available_portions=avail,
                predicted_delivery=pred_del,
                deadline=deadline,
                slack_seconds=slack_sec,
                slack_ratio=slack_ratio,
                risk=risk,
                distance_m=dist_m,
                sub_scores=sub_scores,
                reasons=top_reasons,
            )
        )

    # Sort descending by score
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored


# Step 3: Split Allocation (Wedding-Night Mode)


def plan_allocations(
    donation: MatchDonationSpec,
    scored_candidates: list[ScoredCandidate],
) -> list[SplitAllocation]:
    """
    If top candidate can take everything, return 1 allocation.
    Otherwise, split across top candidates with min_chunk constraint.
    Each allocation receives a distinct container label ("Container A", "Container B", ...).
    """
    if not scored_candidates:
        return []

    remaining_portions = donation.total_portions
    min_chunk = max(10, int(0.20 * donation.total_portions))
    allocations: list[SplitAllocation] = []
    labels = ["Container A", "Container B", "Container C", "Container D", "Container E"]

    # Check if top candidate can take all
    top = scored_candidates[0]
    if top.available_portions >= remaining_portions:
        return [
            SplitAllocation(
                recipient_id=top.candidate.id,
                recipient_name=top.candidate.name,
                recipient_lat=top.candidate.lat,
                recipient_lng=top.candidate.lng,
                portions=remaining_portions,
                container_label="Container A",
                deadline=top.deadline,
                predicted_delivery=top.predicted_delivery,
                slack_seconds=top.slack_seconds,
                risk=top.risk,
                score=top.score,
                reasons=top.reasons,
            )
        ]

    # Split allocation (greedy chunking across top ranked candidates)
    for idx, candidate in enumerate(scored_candidates):
        if remaining_portions <= 0:
            break

        take = min(remaining_portions, candidate.available_portions)
        if take < min_chunk and remaining_portions >= min_chunk:
            continue

        label = labels[idx] if idx < len(labels) else f"Container {chr(65 + idx)}"
        allocations.append(
            SplitAllocation(
                recipient_id=candidate.candidate.id,
                recipient_name=candidate.candidate.name,
                recipient_lat=candidate.candidate.lat,
                recipient_lng=candidate.candidate.lng,
                portions=take,
                container_label=label,
                deadline=candidate.deadline,
                predicted_delivery=candidate.predicted_delivery,
                slack_seconds=candidate.slack_seconds,
                risk=candidate.risk,
                score=candidate.score,
                reasons=candidate.reasons,
            )
        )
        remaining_portions -= take

    return allocations


# Step 4: Offer Cascade Planning


def plan_offer_cascade(
    allocations: list[SplitAllocation],
    scored_candidates: list[ScoredCandidate],
    now: datetime,
) -> list[CascadeOfferPlan]:
    """
    Generate offer cascade:
    - ttl = clamp(0.08 * time_to_deadline, 90 s, 10 min)
    - If slack_ratio < 0.25, offer in parallel to top 2 candidates
    """
    plans: list[CascadeOfferPlan] = []

    for alloc in allocations:
        time_to_deadline = max(0.0, (alloc.deadline - now).total_seconds())
        # ttl = clamp(0.08 * time_to_deadline, 90 s, 600 s)
        ttl = int(max(90.0, min(600.0, 0.08 * time_to_deadline)))

        # Find matching scored candidate to check slack ratio
        matching_cand = next(
            (c for c in scored_candidates if c.candidate.id == alloc.recipient_id), None
        )
        is_parallel = matching_cand is not None and matching_cand.slack_ratio < 0.25

        plans.append(
            CascadeOfferPlan(
                allocation_id=None,
                recipient_id=alloc.recipient_id,
                recipient_name=alloc.recipient_name,
                portions=alloc.portions,
                ttl_seconds=ttl,
                is_parallel=is_parallel,
                score=alloc.score,
            )
        )

    return plans
