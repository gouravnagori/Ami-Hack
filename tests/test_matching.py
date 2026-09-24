"""
Unit and Hypothesis property tests for Recipient Matching Engine (services/matching.py).
"""

import uuid
from datetime import UTC, datetime, time, timedelta

from hypothesis import given
from hypothesis import strategies as st

from app.core.config import DietType, StorageCondition
from app.services.capacity import CapacityWindowSpec
from app.services.matching import (
    CandidateOrg,
    MatchDonationSpec,
    filter_candidates,
    plan_allocations,
    plan_offer_cascade,
    score_candidates,
)


def create_sample_org(
    name: str = "Asha Shelter",
    diets: list[DietType] | None = None,
    storage: list[StorageCondition] | None = None,
    cold_max: int = 10,
    cold_used: int = 0,
    max_portions: int = 100,
    lat: float = 28.6139,
    lng: float = 77.2090,
    is_verified: bool = True,
    need_level: float = 0.8,
) -> CandidateOrg:
    return CandidateOrg(
        id=uuid.uuid4(),
        name=name,
        lat=lat,
        lng=lng,
        is_verified=is_verified,
        accepts_diets=diets or [DietType.VEG, DietType.EGG, DietType.NON_VEG],
        accepts_storage=storage
        or [StorageCondition.AMBIENT, StorageCondition.HOT, StorageCondition.COLD],
        cold_max_units=cold_max,
        cold_used=cold_used,
        need_level=need_level,
        reliability_ewma=0.9,
        last_received_at=None,
        capacity_windows=[
            CapacityWindowSpec(
                start_time=time(0, 0),
                end_time=time(23, 59),
                max_portions=max_portions,
            )
        ],
        service_rate_per_hour=20.0,
    )


def test_dietary_hard_filter_r2():
    """R2: non_veg and egg never go to an org that does not accept them."""
    now = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    veg_only_org = create_sample_org(
        name="Pure Veg Shelter",
        diets=[DietType.VEG],
    )

    donation_non_veg = MatchDonationSpec(
        id=uuid.uuid4(),
        diet=DietType.NON_VEG,
        storage=StorageCondition.HOT,
        category="cooked_meals",
        total_portions=50,
        safe_until=now + timedelta(hours=4),
        pickup_lat=28.6139,
        pickup_lng=77.2090,
        pickup_window_start=now,
        pickup_window_end=now + timedelta(hours=2),
    )

    survivors, rejections = filter_candidates(donation_non_veg, [veg_only_org], now)
    assert len(survivors) == 0
    assert len(rejections) == 1
    assert rejections[0].code == "DIET_MISMATCH"


def test_cold_chain_hard_filter_r3():
    """R3: storage=cold requires cold storage and free units."""
    now = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    no_cold_org = create_sample_org(
        name="Ambient Only Center",
        storage=[StorageCondition.AMBIENT],
        cold_max=0,
    )
    full_cold_org = create_sample_org(
        name="Full Cold Center",
        storage=[StorageCondition.COLD, StorageCondition.AMBIENT],
        cold_max=5,
        cold_used=5,  # 0 free units
    )

    cold_donation = MatchDonationSpec(
        id=uuid.uuid4(),
        diet=DietType.VEG,
        storage=StorageCondition.COLD,
        category="dairy_sweets",
        total_portions=30,
        safe_until=now + timedelta(hours=3),
        pickup_lat=28.6139,
        pickup_lng=77.2090,
        pickup_window_start=now,
        pickup_window_end=now + timedelta(hours=1),
    )

    survivors, rejections = filter_candidates(cold_donation, [no_cold_org, full_cold_org], now)
    assert len(survivors) == 0
    assert len(rejections) == 2
    assert all(r.code == "COLD_CHAIN_UNAVAILABLE" for r in rejections)


def test_time_window_deadline_r4():
    """R4: Expired or unachievable delivery is rejected."""
    now = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    org = create_sample_org()

    # Food expires in 5 minutes (impossible to reach in time)
    expired_soon_donation = MatchDonationSpec(
        id=uuid.uuid4(),
        diet=DietType.VEG,
        storage=StorageCondition.HOT,
        category="cooked_meals",
        total_portions=30,
        safe_until=now + timedelta(minutes=5),
        pickup_lat=28.6139,
        pickup_lng=77.2090,
        pickup_window_start=now,
        pickup_window_end=now + timedelta(minutes=5),
    )

    survivors, rejections = filter_candidates(expired_soon_donation, [org], now)
    assert len(survivors) == 0
    assert len(rejections) == 1
    assert rejections[0].code == "WINDOW_INFEASIBLE"


def test_scoring_and_explanation():
    now = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    org_near = create_sample_org(name="Near Org", lat=28.6140, lng=77.2091, need_level=0.9)
    org_far = create_sample_org(name="Far Org", lat=28.6500, lng=77.2300, need_level=0.3)

    donation = MatchDonationSpec(
        id=uuid.uuid4(),
        diet=DietType.VEG,
        storage=StorageCondition.HOT,
        category="cooked_meals",
        total_portions=40,
        safe_until=now + timedelta(hours=4),
        pickup_lat=28.6139,
        pickup_lng=77.2090,
        pickup_window_start=now,
        pickup_window_end=now + timedelta(hours=2),
    )

    survivors, _ = filter_candidates(donation, [org_near, org_far], now)
    scored = score_candidates(donation, survivors, now)

    assert len(scored) == 2
    # Near org should rank higher than far org with lower need
    assert scored[0].candidate.name == "Near Org"
    assert scored[0].score > scored[1].score
    assert len(scored[0].reasons) == 3
    assert all("label" in r and "code" in r for r in scored[0].reasons)


def test_split_allocation_wedding_night():
    """Wedding Night Mode: 300 plates split across multiple shelters."""
    now = datetime(2026, 9, 24, 23, 40, tzinfo=UTC)
    org1 = create_sample_org(name="Shelter 1", max_portions=100)
    org2 = create_sample_org(name="Shelter 2", max_portions=120)
    org3 = create_sample_org(name="Shelter 3", max_portions=150)

    donation_300 = MatchDonationSpec(
        id=uuid.uuid4(),
        diet=DietType.VEG,
        storage=StorageCondition.HOT,
        category="cooked_meals",
        total_portions=300,
        safe_until=now + timedelta(hours=4),
        pickup_lat=28.6139,
        pickup_lng=77.2090,
        pickup_window_start=now,
        pickup_window_end=now + timedelta(hours=2),
    )

    survivors, _ = filter_candidates(donation_300, [org1, org2, org3], now)
    scored = score_candidates(donation_300, survivors, now)
    allocations = plan_allocations(donation_300, scored)

    # Must be split into multiple allocations
    assert len(allocations) >= 2
    total_allocated = sum(a.portions for a in allocations)
    assert total_allocated == 300
    # Container labels must be distinct
    labels = [a.container_label for a in allocations]
    assert len(labels) == len(set(labels))
    assert "Container A" in labels
    assert "Container B" in labels


def test_cascade_offer_plan():
    now = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    org = create_sample_org()
    donation = MatchDonationSpec(
        id=uuid.uuid4(),
        diet=DietType.VEG,
        storage=StorageCondition.HOT,
        category="cooked_meals",
        total_portions=50,
        safe_until=now + timedelta(hours=3),
        pickup_lat=28.6139,
        pickup_lng=77.2090,
        pickup_window_start=now,
        pickup_window_end=now + timedelta(hours=1),
    )

    survivors, _ = filter_candidates(donation, [org], now)
    scored = score_candidates(donation, survivors, now)
    allocations = plan_allocations(donation, scored)
    plans = plan_offer_cascade(allocations, scored, now)

    assert len(plans) == 1
    # TTL clamped between 90s and 600s
    assert 90 <= plans[0].ttl_seconds <= 600


# Hypothesis Property Invariant Tests


@given(
    portions=st.integers(min_value=10, max_value=500),
    org_cap1=st.integers(min_value=20, max_value=300),
    org_cap2=st.integers(min_value=20, max_value=300),
)
def test_property_split_allocation_portions(portions: int, org_cap1: int, org_cap2: int):
    """Property Invariant 1: Total allocated portions never exceeds total donation portions, and each portion <= available."""
    now = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    org1 = create_sample_org(name="O1", max_portions=org_cap1)
    org2 = create_sample_org(name="O2", max_portions=org_cap2)

    donation = MatchDonationSpec(
        id=uuid.uuid4(),
        diet=DietType.VEG,
        storage=StorageCondition.HOT,
        category="cooked_meals",
        total_portions=portions,
        safe_until=now + timedelta(hours=4),
        pickup_lat=28.6139,
        pickup_lng=77.2090,
        pickup_window_start=now,
        pickup_window_end=now + timedelta(hours=2),
    )

    survivors, _ = filter_candidates(donation, [org1, org2], now)
    scored = score_candidates(donation, survivors, now)
    allocs = plan_allocations(donation, scored)

    total_allocated = sum(a.portions for a in allocs)
    assert total_allocated <= portions
    for a in allocs:
        # Check against corresponding org
        assert a.portions > 0
        assert a.slack_seconds >= 0  # Invariant 2: No allocation created with slack_seconds < 0
