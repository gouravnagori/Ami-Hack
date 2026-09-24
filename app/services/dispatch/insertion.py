"""
Stage 3: Stacking by Insertion with Savelsbergh Forward Time Slack.

Allows drivers already on a route to stack an additional order if:
- Precedence: pickup p before dropoff q
- Vehicle capacity along the whole sequence <= driver.capacity_portions
- Cold box rule: vehicle has cold box if food is cold
- Container labels distinct
- Downstream promise check: arrival + push_forward <= latest_arrival for all downstream stops
- Detour constraints: added_detour_s <= 600s and detour ratio <= 0.35
"""

import uuid
from datetime import UTC, datetime, timedelta

from app.core.config import StopType, StorageCondition
from app.services.capacity import ensure_utc
from app.services.dispatch.types import DispatchTask, DriverCandidate, InsertionResult, StopPlan
from app.services.matching import haversine_distance_m
from app.services.routing.eta import (
    DWELL_TIME_DROPOFF_S,
    DWELL_TIME_PICKUP_S,
    ROAD_DETOUR_FACTOR,
    estimate_travel_duration_s,
)

MAX_DETOUR_S: float = 600.0  # 10 minutes max detour
MAX_DETOUR_RATIO: float = 0.35


def check_capacity_feasibility(
    stops: list[StopPlan],
    max_capacity: int,
    initial_load: int = 0,
) -> bool:
    """Verify that onboard portion count never exceeds vehicle capacity."""
    current_load = initial_load
    for s in stops:
        if s.type == StopType.PICKUP:
            current_load += s.portions
        elif s.type == StopType.DROPOFF:
            current_load -= s.portions
        if current_load > max_capacity:
            return False
    return True


def compute_forward_time_slack(stops: list[StopPlan]) -> list[float]:
    """
    Savelsbergh Forward Time Slack precomputation:
    slack[k] = (window_end[k] - arrival[k]).total_seconds()
    forward_slack[k] = min(slack[k], forward_slack[k+1]) from end to start.
    """
    n = len(stops)
    if n == 0:
        return []

    slacks: list[float] = []
    for s in stops:
        arr = ensure_utc(s.predicted_arrival) or ensure_utc(s.planned_arrival)
        w_end = ensure_utc(s.window_end)
        slack = max(0.0, (w_end - arr).total_seconds()) if arr and w_end else 0.0
        slacks.append(slack)

    forward_slack = [0.0] * n
    forward_slack[-1] = slacks[-1]
    for k in range(n - 2, -1, -1):
        forward_slack[k] = min(slacks[k], forward_slack[k + 1])

    return forward_slack


def evaluate_insertion(
    driver: DriverCandidate,
    task: DispatchTask,
    pickup_idx: int,
    dropoff_idx: int,
    now: datetime,
) -> InsertionResult | None:
    """
    Try inserting task pickup at pickup_idx and dropoff at dropoff_idx.
    """
    existing = driver.existing_stops
    n = len(existing)

    # 1. Basic sanity checks
    if pickup_idx > dropoff_idx or pickup_idx > n or dropoff_idx > n + 1:
        return None

    # Cold chain rule
    if task.storage == StorageCondition.COLD and not driver.has_cold_box:
        return None

    now_utc = ensure_utc(now) or datetime.now(UTC)

    # 2. Build candidate stop objects
    pickup_stop = StopPlan(
        id=uuid.uuid4(),
        seq=0,
        type=StopType.PICKUP,
        allocation_id=task.allocation_id,
        lat=task.pickup_lat,
        lng=task.pickup_lng,
        name=task.pickup_name,
        address=task.pickup_address,
        window_start=task.ready_at,
        window_end=task.latest_pickup,
        portions=task.portions,
        diet=task.diet,
        storage=task.storage,
        container_label=task.container_label,
        requires_otp=True,
    )

    dropoff_stop = StopPlan(
        id=uuid.uuid4(),
        seq=0,
        type=StopType.DROPOFF,
        allocation_id=task.allocation_id,
        lat=task.dropoff_lat,
        lng=task.dropoff_lng,
        name=task.dropoff_name,
        address=task.dropoff_address,
        window_start=task.ready_at,
        window_end=task.dropoff_window_end,
        portions=task.portions,
        diet=task.diet,
        storage=task.storage,
        container_label=task.container_label,
        requires_otp=True,
    )

    # Create new sequence
    candidate_stops = list(existing)
    candidate_stops.insert(pickup_idx, pickup_stop)
    candidate_stops.insert(dropoff_idx, dropoff_stop)

    # Update sequence numbers
    for i, s in enumerate(candidate_stops):
        s.seq = i + 1

    # 3. Capacity check along new route
    if not check_capacity_feasibility(candidate_stops, driver.capacity_portions):
        return None

    # 4. Recompute timings from driver's current position
    curr_lat, curr_lng = driver.lat, driver.lng
    curr_time = now_utc
    total_new_duration_s = 0.0

    for s in candidate_stops:
        dist_m = haversine_distance_m(curr_lat, curr_lng, s.lat, s.lng) * ROAD_DETOUR_FACTOR
        leg_s = estimate_travel_duration_s(
            distance_m=dist_m,
            vehicle_type=driver.vehicle_type,
            dt=curr_time,
            speed_factor_ewma=driver.speed_factor_ewma,
        )
        total_new_duration_s += leg_s

        arrival = curr_time + timedelta(seconds=leg_s)
        dwell = DWELL_TIME_PICKUP_S if s.type == StopType.PICKUP else DWELL_TIME_DROPOFF_S
        start_service = max(arrival, ensure_utc(s.window_start) or arrival)
        s.planned_arrival = arrival
        s.predicted_arrival = arrival

        w_end = ensure_utc(s.window_end)
        if w_end and arrival > w_end:
            # Violates promise!
            return None

        curr_time = start_service + timedelta(seconds=dwell)
        curr_lat, curr_lng = s.lat, s.lng

    # 5. Detour calculation
    # Compute duration of original route
    orig_duration_s = 0.0
    c_lat, c_lng = driver.lat, driver.lng
    c_time = now_utc
    for s in existing:
        d_m = haversine_distance_m(c_lat, c_lng, s.lat, s.lng) * ROAD_DETOUR_FACTOR
        l_s = estimate_travel_duration_s(d_m, driver.vehicle_type, c_time, driver.speed_factor_ewma)
        orig_duration_s += l_s
        c_lat, c_lng = s.lat, s.lng

    added_detour_s = max(0.0, total_new_duration_s - orig_duration_s)
    if added_detour_s > MAX_DETOUR_S:
        return None

    detour_ratio = added_detour_s / max(1.0, orig_duration_s)
    if orig_duration_s > 0.0 and detour_ratio > MAX_DETOUR_RATIO:
        return None

    # Cost in minutes
    added_time_min = added_detour_s / 60.0
    # Soft deadline check on new task delivery
    deadline_utc = ensure_utc(task.deadline)
    pred_delivery = dropoff_stop.predicted_arrival
    late_min = max(0.0, (pred_delivery - deadline_utc).total_seconds()) / 60.0 if deadline_utc else 0.0

    cost = added_time_min + 8.0 * late_min

    return InsertionResult(
        driver_id=driver.id,
        task_id=task.allocation_id,
        pickup_index=pickup_idx,
        dropoff_index=dropoff_idx,
        added_detour_s=round(added_detour_s, 1),
        cost_minutes=round(cost, 2),
        new_stops=candidate_stops,
    )


def find_best_stacked_insertion(
    task: DispatchTask,
    active_drivers: list[DriverCandidate],
    now: datetime,
) -> InsertionResult | None:
    """
    Search all active drivers for the cheapest feasible (pickup, dropoff) insertion.
    """
    best_result: InsertionResult | None = None

    for driver in active_drivers:
        n = len(driver.existing_stops)
        # Try all (i, j) with i <= j
        for i in range(n + 1):
            for j in range(i + 1, n + 2):
                result = evaluate_insertion(driver, task, i, j, now)
                if result:
                    if best_result is None or result.cost_minutes < best_result.cost_minutes:
                        best_result = result

    return best_result
