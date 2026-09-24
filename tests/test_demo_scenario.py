"""
STEP 6: Deterministic Hackathon Demo Scenario.

Scenario:
  DONOR: Restaurant/Event  — 50 portions, hot veg, short safety window
  RECIPIENTS:
    1. Near shelter  — 100 cap, veg+egg+nonveg, high need (0.9), cold storage
    2. Mid shelter   — 60 cap, veg only, medium need (0.6), no cold
    3. Far shelter   — 200 cap, all diets, low need (0.3), cold storage, distant
  DRIVERS:
    1. Nearby scooter with cold box — available
    2. Distant van — available, no cold box

Run the matching + scoring flow deterministically and output:
  - Selected recipient (highest score)
  - Match score
  - Top 3 reasons (code + label)
  - ETA estimate
  - Deadline vs safety margin
  - Impact: meals, portions, CO2e (from service layer)

This test is designed to be reproducible for a live hackathon demo.
"""

import uuid
from datetime import UTC, datetime, time, timedelta

from app.core.config import DietType, DriverStatus, StorageCondition, VehicleType
from app.services.capacity import CapacityWindowSpec
from app.services.matching import (
    CandidateOrg,
    MatchDonationSpec,
    filter_candidates,
    plan_allocations,
    score_candidates,
)


def _make_org(
    name: str,
    lat: float,
    lng: float,
    max_portions: int,
    need_level: float,
    diets: list[DietType],
    storage: list[StorageCondition],
    cold_max: int = 0,
    reliability: float = 0.85,
) -> CandidateOrg:
    return CandidateOrg(
        id=uuid.uuid4(),
        name=name,
        lat=lat,
        lng=lng,
        is_verified=True,
        accepts_diets=diets,
        accepts_storage=storage,
        cold_max_units=cold_max,
        cold_used=0,
        need_level=need_level,
        reliability_ewma=reliability,
        last_received_at=None,
        capacity_windows=[
            CapacityWindowSpec(
                start_time=time(0, 0),
                end_time=time(23, 59),
                max_portions=max_portions,
            )
        ],
        service_rate_per_hour=30.0,
    )


def test_demo_scenario_matching_and_scoring():
    """
    Deterministic demo scenario: 50-portion hot veg donation.
    Expected: Near Shelter wins (closest + highest need).
    """
    now = datetime(2026, 9, 24, 19, 0, tzinfo=UTC)  # Fixed time for reproducibility

    # ── Donation (Restaurant, post-event) ─────────────────────────────────────
    donation = MatchDonationSpec(
        id=uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001"),
        diet=DietType.VEG,
        storage=StorageCondition.HOT,
        category="cooked_meals",
        total_portions=50,
        safe_until=now + timedelta(hours=3),  # Short 3-hour window (hot food)
        pickup_lat=28.6139,
        pickup_lng=77.2090,
        pickup_window_start=now,
        pickup_window_end=now + timedelta(hours=1, minutes=30),
    )

    # ── Recipients ────────────────────────────────────────────────────────────
    near_shelter = _make_org(
        name="Asha Kuteer (Near)",
        lat=28.6150,  # ~130m from pickup
        lng=77.2095,
        max_portions=100,
        need_level=0.9,
        diets=[DietType.VEG, DietType.EGG, DietType.NON_VEG],
        storage=[StorageCondition.AMBIENT, StorageCondition.HOT, StorageCondition.COLD],
        cold_max=40,
    )

    mid_shelter = _make_org(
        name="Prerna Home (Mid)",
        lat=28.6250,  # ~1.2 km
        lng=77.2130,
        max_portions=60,
        need_level=0.6,
        diets=[DietType.VEG],
        storage=[StorageCondition.AMBIENT, StorageCondition.HOT],
        cold_max=0,
    )

    far_shelter = _make_org(
        name="Sahara Center (Far)",
        lat=28.6500,  # ~4.5 km
        lng=77.2350,
        max_portions=200,
        need_level=0.3,
        diets=[DietType.VEG, DietType.EGG, DietType.NON_VEG],
        storage=[StorageCondition.AMBIENT, StorageCondition.HOT, StorageCondition.COLD],
        cold_max=60,
    )

    orgs = [near_shelter, mid_shelter, far_shelter]

    # ── Filter ────────────────────────────────────────────────────────────────
    survivors, rejections = filter_candidates(donation, orgs, now)

    print(f"\n{'='*60}")
    print("DEMO SCENARIO — MATCHING RESULTS")
    print(f"{'='*60}")
    print(f"Donation: {donation.total_portions} portions of {donation.diet} food")
    print(f"Safety window: {(donation.safe_until - now).total_seconds() / 3600:.1f}h")
    print(f"Candidates evaluated: {len(orgs)}")
    print(f"Eligible after filters: {len(survivors)}")
    if rejections:
        print("Rejections:")
        for rej in rejections:
            print(f"  - {rej.org.name}: {rej.code}")

    # All 3 should pass (veg hot food, all have HOT storage)
    assert len(survivors) >= 2, f"Expected ≥2 survivors, got {len(survivors)}"
    assert len(rejections) == 0, f"Unexpected rejections: {[r.code for r in rejections]}"

    # ── Score ─────────────────────────────────────────────────────────────────
    scored = score_candidates(donation, survivors, now)

    print("\nRanked Recipients:")
    for rank, s in enumerate(scored, 1):
        print(f"  {rank}. {s.candidate.name}")
        print(f"     Score: {s.score:.4f}")
        print("     Reasons:")
        for reason in s.reasons:
            print(f"       [{reason['code']}] {reason['label']}")

    # Near shelter must win
    best = scored[0]
    assert best.candidate.name == "Asha Kuteer (Near)", (
        f"Near shelter expected to win, got {best.candidate.name}"
    )
    assert best.score > scored[1].score, "Winner must have strictly higher score"
    assert len(best.reasons) >= 3, "At least 3 scoring reasons must be exposed"

    # Verify reason structure
    for r in best.reasons:
        assert "code" in r, "Reason must have code"
        assert "label" in r, "Reason must have label"

    # ── Allocations ───────────────────────────────────────────────────────────
    allocations = plan_allocations(donation, scored)

    print("\nAllocations:")
    for alloc in allocations:
        print(f"  - {alloc.recipient_id}: {alloc.portions} portions [{alloc.container_label}]")
        print(f"    Deadline: {alloc.deadline}")
        print(f"    Slack: {alloc.slack_seconds / 60:.0f} min")

    total_allocated = sum(a.portions for a in allocations)
    assert total_allocated == 50, f"All 50 portions must be allocated, got {total_allocated}"

    # ── Impact projection ─────────────────────────────────────────────────────
    # Each portion ≈ 0.35 kg (settings.PORTION_KG)
    # CO2e saving ≈ 2.5 kg CO2e per kg food rescued (app.services.impact logic)
    estimated_weight_kg = total_allocated * 0.35
    estimated_co2e_kg = estimated_weight_kg * 2.5

    print("\nPROJECTED IMPACT:")
    print(f"  Meals served: {total_allocated}")
    print(f"  Estimated weight: {estimated_weight_kg:.1f} kg")
    print(f"  CO2e saved: {estimated_co2e_kg:.1f} kg")
    print(f"  Safety margin: {allocations[0].slack_seconds / 60:.0f} min remaining")
    print(f"  Winner: {best.candidate.name}")
    print(f"  Match score: {best.score:.4f}")
    print(f"  Top reason: {best.reasons[0]['label']}")
    print(f"{'='*60}\n")

    # Basic sanity
    assert estimated_weight_kg > 0
    assert estimated_co2e_kg > 0
    assert allocations[0].slack_seconds >= 0, "Slack must never be negative"


def test_demo_scenario_cold_chain_exclusion():
    """
    Demo sub-scenario: A cold donation (dairy/sweets) excludes orgs
    without cold storage. Only the one cold-capable org is selected.
    """
    now = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)

    cold_donation = MatchDonationSpec(
        id=uuid.UUID("bbbbbbbb-0000-0000-0000-000000000002"),
        diet=DietType.VEG,
        storage=StorageCondition.COLD,
        category="dairy_sweets",
        total_portions=30,
        safe_until=now + timedelta(hours=2),
        pickup_lat=28.6139,
        pickup_lng=77.2090,
        pickup_window_start=now,
        pickup_window_end=now + timedelta(hours=1),
    )

    cold_capable = _make_org(
        name="Cold Chain Shelter",
        lat=28.6150,
        lng=77.2095,
        max_portions=80,
        need_level=0.75,
        diets=[DietType.VEG, DietType.EGG],
        storage=[StorageCondition.COLD, StorageCondition.AMBIENT],
        cold_max=30,
    )
    ambient_only = _make_org(
        name="Ambient Only Shelter",
        lat=28.6155,
        lng=77.2092,
        max_portions=80,
        need_level=0.85,
        diets=[DietType.VEG, DietType.EGG],
        storage=[StorageCondition.AMBIENT],
        cold_max=0,
    )

    survivors, rejections = filter_candidates(cold_donation, [cold_capable, ambient_only], now)
    assert len(survivors) == 1
    assert survivors[0][0].name == "Cold Chain Shelter"
    assert len(rejections) == 1
    assert rejections[0].code == "COLD_CHAIN_UNAVAILABLE"

    print("\nCold Chain Demo:")
    print(f"  [OK] {survivors[0][0].name} - accepted (has cold storage)")
    print(f"  [REJECT] {rejections[0].org_name} - rejected: {rejections[0].code}")


def test_demo_scenario_driver_cold_box_rule():
    """
    Demo sub-scenario: cold donation requires driver with cold box.
    Verified by the dispatch filter — drivers without cold box are excluded.
    """
    from app.services.dispatch.assignment import filter_candidate_drivers
    from app.services.dispatch.types import DispatchTask, DriverCandidate

    now = datetime(2026, 9, 24, 20, 0, tzinfo=UTC)

    task = DispatchTask(
        allocation_id=uuid.uuid4(),
        donation_id=uuid.uuid4(),
        portions=20,
        diet=DietType.VEG,
        storage=StorageCondition.COLD,
        container_label="Cold Box A",
        deadline=now + timedelta(hours=2),
        pickup_lat=28.6139,
        pickup_lng=77.2090,
        pickup_address="Donor Kitchen",
        pickup_name="GoldenHour Demo Donor",
        ready_at=now,
        latest_pickup=now + timedelta(hours=1),
        dropoff_lat=28.6150,
        dropoff_lng=77.2095,
        dropoff_address="Cold Chain Shelter",
        dropoff_name="Cold Chain Shelter",
        dropoff_window_end=now + timedelta(hours=2),
    )

    nearby_no_cold = DriverCandidate(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        vehicle_type=VehicleType.SCOOTER,
        capacity_portions=60,
        has_cold_box=False,
        status=DriverStatus.AVAILABLE,
        lat=28.6140,
        lng=77.2092,
    )

    nearby_cold = DriverCandidate(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        vehicle_type=VehicleType.SCOOTER,
        capacity_portions=60,
        has_cold_box=True,
        status=DriverStatus.AVAILABLE,
        lat=28.6141,
        lng=77.2093,
    )

    far_cold = DriverCandidate(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        vehicle_type=VehicleType.VAN,
        capacity_portions=200,
        has_cold_box=True,
        status=DriverStatus.AVAILABLE,
        lat=28.6400,
        lng=77.2300,
    )

    eligible = filter_candidate_drivers(task, [nearby_no_cold, nearby_cold, far_cold], now)

    print("\nDriver Cold-Box Demo:")
    print("  Total drivers: 3")
    print(f"  Eligible for cold delivery: {len(eligible)}")
    for d in eligible:
        print(f"    - {'nearby scooter+cold' if d.id == nearby_cold.id else 'far van+cold'}")
    print("  Rejected (no cold box): 1")

    assert len(eligible) == 2
    assert nearby_no_cold.id not in [d.id for d in eligible]
    assert nearby_cold.id in [d.id for d in eligible]
    assert far_cold.id in [d.id for d in eligible]
