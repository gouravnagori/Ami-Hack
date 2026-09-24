"""
Safety and time-window engine — pure business logic.

All business rules live in pure functions (inputs in, decision out, `now` injected).
Enforces:
- R3: Cold chain & hot food transit caps
- R4: Time window & safe_until limits
- Risk classification (safe, tight, critical, infeasible)
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.config import Risk, StorageCondition


def ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


@dataclass(frozen=True)
class SafetyRuleSpec:
    storage: StorageCondition
    category: str
    max_hours: float
    transit_cap_minutes: int
    handling_buffer_minutes: int


# Default fallback safety rules (placeholder values seeded per spec)
# -- VALIDATE WITH FSSAI / LOCAL FOOD-SAFETY GUIDANCE BEFORE PILOT
DEFAULT_SAFETY_RULES: dict[tuple[StorageCondition, str], SafetyRuleSpec] = {
    (StorageCondition.HOT, "cooked_meals"): SafetyRuleSpec(
        storage=StorageCondition.HOT,
        category="cooked_meals",
        max_hours=4.0,
        transit_cap_minutes=60,
        handling_buffer_minutes=15,
    ),
    (StorageCondition.COLD, "dairy_sweets"): SafetyRuleSpec(
        storage=StorageCondition.COLD,
        category="dairy_sweets",
        max_hours=3.0,
        transit_cap_minutes=45,
        handling_buffer_minutes=15,
    ),
    (StorageCondition.COLD, "cooked_meals"): SafetyRuleSpec(
        storage=StorageCondition.COLD,
        category="cooked_meals",
        max_hours=4.0,
        transit_cap_minutes=60,
        handling_buffer_minutes=15,
    ),
    (StorageCondition.AMBIENT, "packaged"): SafetyRuleSpec(
        storage=StorageCondition.AMBIENT,
        category="packaged",
        max_hours=24.0,
        transit_cap_minutes=120,
        handling_buffer_minutes=30,
    ),
    (StorageCondition.AMBIENT, "cooked_meals"): SafetyRuleSpec(
        storage=StorageCondition.AMBIENT,
        category="cooked_meals",
        max_hours=4.0,
        transit_cap_minutes=60,
        handling_buffer_minutes=15,
    ),
}


def get_default_safety_rule(
    storage: StorageCondition, category: str = "cooked_meals"
) -> SafetyRuleSpec:
    """Retrieve fallback safety rule for given storage and category."""
    key = (storage, category)
    if key in DEFAULT_SAFETY_RULES:
        return DEFAULT_SAFETY_RULES[key]
    # Generic fallback based on storage
    if storage == StorageCondition.HOT:
        return SafetyRuleSpec(storage, category, 4.0, 60, 15)
    elif storage == StorageCondition.COLD:
        return SafetyRuleSpec(storage, category, 4.0, 60, 15)
    else:
        return SafetyRuleSpec(storage, category, 12.0, 120, 20)


def compute_safe_until(
    prepared_at: datetime,
    best_before: datetime | None,
    max_hours: float,
    donor_safe_until: datetime | None = None,
) -> datetime:
    """
    safe_until = min(donor_best_before, prepared_at + rule.max_hours(storage, category))
    Donors may shorten safe_until, never extend it.
    """
    rule_cap = prepared_at + timedelta(hours=max_hours)
    candidate = rule_cap
    if best_before is not None and best_before < candidate:
        candidate = best_before

    if donor_safe_until is not None and donor_safe_until < candidate:
        # Donor may shorten safe_until, never extend it
        candidate = donor_safe_until

    return candidate


def compute_deadline(
    safe_until: datetime,
    recipient_window_end: datetime,
    handling_buffer_minutes: int = 15,
) -> datetime:
    """
    deadline(alloc) = min(donation.safe_until, recipient_window_end) - handling_buffer(storage, category)
    """
    effective_end = min(ensure_utc(safe_until), ensure_utc(recipient_window_end))
    return effective_end - timedelta(minutes=handling_buffer_minutes)


def compute_predicted_delivery(
    now: datetime,
    eta_to_pickup_seconds: float,
    eta_pickup_to_dropoff_seconds: float,
    wait_for_pickup_seconds: float = 0.0,
    pickup_service_seconds: float = 300.0,
    dropoff_service_seconds: float = 300.0,
) -> datetime:
    """
    predicted_delivery = now + wait_for_pickup + eta(driver->pickup) + pickup_service
                            + eta(pickup->dropoff) + dropoff_service
    """
    total_seconds = (
        wait_for_pickup_seconds
        + eta_to_pickup_seconds
        + pickup_service_seconds
        + eta_pickup_to_dropoff_seconds
        + dropoff_service_seconds
    )
    return ensure_utc(now) + timedelta(seconds=total_seconds)


def compute_slack(
    deadline: datetime,
    predicted_delivery: datetime,
    now: datetime,
) -> tuple[float, float]:
    """
    slack_seconds = deadline - predicted_delivery
    slack_ratio   = slack_seconds / (deadline - now)

    Returns (slack_seconds, slack_ratio)
    """
    d_utc = ensure_utc(deadline)
    p_utc = ensure_utc(predicted_delivery)
    n_utc = ensure_utc(now)

    slack_seconds = (d_utc - p_utc).total_seconds()
    total_window_seconds = (d_utc - n_utc).total_seconds()

    if total_window_seconds <= 0:
        slack_ratio = 1.0 if slack_seconds >= 0 else -1.0
    else:
        slack_ratio = slack_seconds / total_window_seconds

    return slack_seconds, slack_ratio


def classify_risk(slack_seconds: float, total_window_seconds: float) -> Risk:
    """
    risk = safe if slack_ratio > 0.30 · tight if 0.10–0.30 · critical if < 0.10 · infeasible if slack < 0
    Returns Risk enum (Risk.SAFE, Risk.TIGHT, Risk.CRITICAL).
    Note: When slack_seconds < 0, it is infeasible, which maps to CRITICAL with negative slack.
    """
    if slack_seconds < 0:
        return Risk.CRITICAL

    if total_window_seconds <= 0:
        return Risk.CRITICAL

    ratio = slack_seconds / total_window_seconds
    if ratio > 0.30:
        return Risk.SAFE
    elif ratio >= 0.10:
        return Risk.TIGHT
    else:
        return Risk.CRITICAL


def is_feasible(
    predicted_delivery: datetime,
    deadline: datetime,
    transit_duration_seconds: float,
    transit_cap_minutes: int,
) -> bool:
    """
    Check if an allocation/delivery leg is strictly feasible:
    1. predicted_delivery <= deadline (i.e. slack_seconds >= 0)
    2. transit_duration_seconds <= transit_cap_minutes * 60
    """
    p_utc = ensure_utc(predicted_delivery)
    d_utc = ensure_utc(deadline)
    if p_utc > d_utc:
        return False

    max_transit_seconds = transit_cap_minutes * 60
    if transit_duration_seconds > max_transit_seconds:
        return False

    return True
