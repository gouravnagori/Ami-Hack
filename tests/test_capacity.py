"""
Unit and Hypothesis property tests for Capacity Engine (services/capacity.py).
"""

from datetime import UTC, datetime, time, timedelta

from hypothesis import given
from hypothesis import strategies as st

from app.services.capacity import (
    CapacityWindowSpec,
    ReservationSpec,
    compute_available_capacity,
    compute_committed_before,
    compute_projected_stock,
    is_window_covering,
)


def test_window_matching():
    win = CapacityWindowSpec(
        start_time=time(10, 0),
        end_time=time(22, 0),
        max_portions=150,
        dow=3,  # Thursday
    )
    # Thursday at 14:00
    target_thurs = datetime(2026, 9, 24, 14, 0, tzinfo=UTC)
    assert is_window_covering(win, target_thurs)

    # Friday at 14:00 (dow=4)
    target_fri = datetime(2026, 9, 25, 14, 0, tzinfo=UTC)
    assert not is_window_covering(win, target_fri)


def test_projected_stock_depletion():
    now = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    in_stock = 60.0
    service_rate = 20.0  # 20 portions/hour

    # At now
    assert compute_projected_stock(in_stock, service_rate, now, now) == 60.0

    # 1 hour later -> 40 left
    t1 = now + timedelta(hours=1)
    assert compute_projected_stock(in_stock, service_rate, now, t1) == 40.0

    # 3 hours later -> 0 left
    t3 = now + timedelta(hours=3)
    assert compute_projected_stock(in_stock, service_rate, now, t3) == 0.0

    # 5 hours later -> still 0 (does not go negative)
    t5 = now + timedelta(hours=5)
    assert compute_projected_stock(in_stock, service_rate, now, t5) == 0.0


def test_committed_before_summation():
    now = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    t_arrive = now + timedelta(hours=1)

    reservations = [
        ReservationSpec(
            portions=30,
            cold_units=0,
            state="held",
            held_until=now + timedelta(minutes=15),
            arrives_at=now + timedelta(minutes=45),
        ),
        ReservationSpec(
            portions=20,
            cold_units=0,
            state="committed",
            held_until=None,
            arrives_at=now + timedelta(minutes=50),
        ),
        # Arrives AFTER target_time -> should not be included
        ReservationSpec(
            portions=40,
            cold_units=0,
            state="committed",
            held_until=None,
            arrives_at=now + timedelta(hours=2),
        ),
        # Held but EXPIRED -> should not be included
        ReservationSpec(
            portions=50,
            cold_units=0,
            state="held",
            held_until=now - timedelta(minutes=5),
            arrives_at=now + timedelta(minutes=30),
        ),
    ]

    comm = compute_committed_before(reservations, t_arrive, now)
    assert comm == 30 + 20  # 50 portions


def test_available_capacity_calculation():
    # max 100, projected 30, committed 20 -> available 50
    avail = compute_available_capacity(
        window_max=100,
        projected_stock=30.0,
        committed_before=20,
        is_closed_or_full=False,
    )
    assert avail == 50

    # Closed or marked full -> 0
    assert (
        compute_available_capacity(
            window_max=100,
            projected_stock=30.0,
            committed_before=20,
            is_closed_or_full=True,
        )
        == 0
    )


# Hypothesis property test


@given(
    window_max=st.integers(min_value=0, max_value=1000),
    projected_stock=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False),
    committed=st.integers(min_value=0, max_value=1000),
    is_closed=st.booleans(),
)
def test_property_available_capacity_non_negative(
    window_max: int, projected_stock: float, committed: int, is_closed: bool
):
    """Property invariant: Available capacity is always non-negative and <= window_max."""
    avail = compute_available_capacity(
        window_max=window_max,
        projected_stock=projected_stock,
        committed_before=committed,
        is_closed_or_full=is_closed,
    )
    assert avail >= 0
    assert avail <= window_max
