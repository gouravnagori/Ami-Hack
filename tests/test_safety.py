"""
Unit and Hypothesis property tests for Safety and Time-Window Engine (services/safety.py).
"""

from datetime import UTC, datetime, timedelta

from hypothesis import given
from hypothesis import strategies as st

from app.core.config import Risk, StorageCondition
from app.services.safety import (
    classify_risk,
    compute_deadline,
    compute_predicted_delivery,
    compute_safe_until,
    get_default_safety_rule,
    is_feasible,
)


def test_default_safety_rules():
    hot_rule = get_default_safety_rule(StorageCondition.HOT, "cooked_meals")
    assert hot_rule.max_hours == 4.0
    assert hot_rule.transit_cap_minutes == 60
    assert hot_rule.handling_buffer_minutes == 15

    cold_rule = get_default_safety_rule(StorageCondition.COLD, "dairy_sweets")
    assert cold_rule.max_hours == 3.0
    assert cold_rule.transit_cap_minutes == 45
    assert cold_rule.handling_buffer_minutes == 15

    ambient_rule = get_default_safety_rule(StorageCondition.AMBIENT, "packaged")
    assert ambient_rule.max_hours == 24.0
    assert ambient_rule.transit_cap_minutes == 120
    assert ambient_rule.handling_buffer_minutes == 30


def test_compute_safe_until():
    now = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    # Default 4 hours
    safe_until = compute_safe_until(prepared_at=now, best_before=None, max_hours=4.0)
    assert safe_until == now + timedelta(hours=4)

    # Shorter best before
    shorter_bb = now + timedelta(hours=2)
    safe_until_bb = compute_safe_until(prepared_at=now, best_before=shorter_bb, max_hours=4.0)
    assert safe_until_bb == shorter_bb

    # Donor shortening safe_until
    donor_short = now + timedelta(hours=1, minutes=30)
    safe_until_donor = compute_safe_until(
        prepared_at=now, best_before=None, max_hours=4.0, donor_safe_until=donor_short
    )
    assert safe_until_donor == donor_short

    # Donor attempting to extend safe_until (must be ignored/capped at rule limit)
    donor_extend = now + timedelta(hours=6)
    safe_until_capped = compute_safe_until(
        prepared_at=now, best_before=None, max_hours=4.0, donor_safe_until=donor_extend
    )
    assert safe_until_capped == now + timedelta(hours=4)


def test_compute_deadline():
    safe_until = datetime(2026, 9, 24, 16, 0, tzinfo=UTC)
    recipient_close = datetime(2026, 9, 24, 18, 0, tzinfo=UTC)

    # Capped by safe_until - buffer
    dl1 = compute_deadline(safe_until, recipient_close, handling_buffer_minutes=15)
    assert dl1 == safe_until - timedelta(minutes=15)

    # Capped by recipient close - buffer
    early_close = datetime(2026, 9, 24, 15, 0, tzinfo=UTC)
    dl2 = compute_deadline(safe_until, early_close, handling_buffer_minutes=15)
    assert dl2 == early_close - timedelta(minutes=15)


def test_compute_predicted_delivery():
    now = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    pred = compute_predicted_delivery(
        now=now,
        eta_to_pickup_seconds=600,  # 10 min
        eta_pickup_to_dropoff_seconds=1200,  # 20 min
        wait_for_pickup_seconds=0,
        pickup_service_seconds=300,  # 5 min
        dropoff_service_seconds=300,  # 5 min
    )
    assert pred == now + timedelta(seconds=2400)  # 40 min total


def test_is_feasible():
    deadline = datetime(2026, 9, 24, 14, 0, tzinfo=UTC)
    on_time = datetime(2026, 9, 24, 13, 30, tzinfo=UTC)
    late = datetime(2026, 9, 24, 14, 15, tzinfo=UTC)

    # Feasible leg
    assert is_feasible(
        predicted_delivery=on_time,
        deadline=deadline,
        transit_duration_seconds=1800,  # 30 min
        transit_cap_minutes=60,
    )

    # Infeasible: late delivery
    assert not is_feasible(
        predicted_delivery=late,
        deadline=deadline,
        transit_duration_seconds=1800,
        transit_cap_minutes=60,
    )

    # Infeasible: transit cap exceeded
    assert not is_feasible(
        predicted_delivery=on_time,
        deadline=deadline,
        transit_duration_seconds=4000,  # > 60 min
        transit_cap_minutes=60,
    )


# Property tests using Hypothesis


@given(
    slack_seconds=st.floats(
        min_value=-3600.0, max_value=7200.0, allow_nan=False, allow_infinity=False
    ),
    total_window_seconds=st.floats(
        min_value=1.0, max_value=7200.0, allow_nan=False, allow_infinity=False
    ),
)
def test_property_risk_classification(slack_seconds: float, total_window_seconds: float):
    risk = classify_risk(slack_seconds, total_window_seconds)
    ratio = slack_seconds / total_window_seconds

    if slack_seconds < 0 or ratio < 0.10:
        assert risk == Risk.CRITICAL
    elif ratio <= 0.30:
        assert risk == Risk.TIGHT
    else:
        assert risk == Risk.SAFE


@given(
    slack_a=st.floats(min_value=0.0, max_value=3600.0, allow_nan=False, allow_infinity=False),
    slack_b=st.floats(min_value=0.0, max_value=3600.0, allow_nan=False, allow_infinity=False),
    total_window=st.floats(min_value=60.0, max_value=7200.0, allow_nan=False, allow_infinity=False),
)
def test_property_risk_monotonic_in_slack(slack_a: float, slack_b: float, total_window: float):
    """Property invariant: Risk is monotone in slack (greater slack -> equal or better safety)."""
    if slack_a > slack_b:
        slack_a, slack_b = slack_b, slack_a

    # slack_a <= slack_b
    risk_a = classify_risk(slack_a, total_window)
    risk_b = classify_risk(slack_b, total_window)

    severity_order = {Risk.CRITICAL: 0, Risk.TIGHT: 1, Risk.SAFE: 2}
    assert severity_order[risk_a] <= severity_order[risk_b]
