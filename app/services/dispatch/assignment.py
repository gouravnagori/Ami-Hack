"""
Stage 1 & Stage 2: Candidate Driver Filter and Min-Cost Bipartite Assignment.

Implements:
- Candidate driver filter (GPS freshness, service radius, capacity, cold box, active offer check)
- Cost matrix calculation in minutes with weights:
    w_pick=1.0, w_late=8.0, w_acc=0.6, w_load=0.3, w_risk=-2.0 for critical
- Bipartite matching using scipy.optimize.linear_sum_assignment
"""

from datetime import UTC, datetime, timedelta

import numpy as np
from scipy.optimize import linear_sum_assignment

from app.core.config import DriverStatus, Risk, StorageCondition
from app.services.capacity import ensure_utc
from app.services.dispatch.types import AssignmentResult, DispatchTask, DriverCandidate
from app.services.matching import haversine_distance_m
from app.services.routing.eta import (
    DWELL_TIME_DROPOFF_S,
    DWELL_TIME_PICKUP_S,
    estimate_travel_duration_s,
)

INFEASIBLE_COST: float = 1e6
MAX_CANDIDATES_PER_TASK: int = 15


def filter_candidate_drivers(
    task: DispatchTask,
    drivers: list[DriverCandidate],
    now: datetime,
    max_candidates: int = MAX_CANDIDATES_PER_TASK,
) -> list[DriverCandidate]:
    """
    Stage 1: Filter eligible drivers for a task:
    - Status in {available, on_task}
    - GPS within service radius
    - Capacity sufficient
    - Cold box rule (R3) if storage=cold
    """
    survivors: list[tuple[float, DriverCandidate]] = []

    for d in drivers:
        if d.status not in (DriverStatus.AVAILABLE, DriverStatus.ON_TASK):
            continue

        # Rule R3: Cold food requires vehicle with cold box
        if task.storage == StorageCondition.COLD and not d.has_cold_box:
            continue

        # Vehicle capacity check
        if task.portions > d.capacity_portions:
            continue

        # Distance to pickup
        dist_m = haversine_distance_m(d.lat, d.lng, task.pickup_lat, task.pickup_lng)
        if dist_m > d.service_radius_m:
            continue

        survivors.append((dist_m, d))

    # Keep best N by straight-line distance
    survivors.sort(key=lambda x: x[0])
    return [d for _, d in survivors[:max_candidates]]


def compute_driver_task_cost(
    driver: DriverCandidate,
    task: DispatchTask,
    now: datetime,
) -> tuple[float, float, datetime]:
    """
    Compute dispatch cost in minutes for driver d and task t.
    Returns: (cost_minutes, pickup_eta_min, predicted_delivery)
    """
    now_utc = ensure_utc(now) or datetime.now(UTC)
    deadline_utc = ensure_utc(task.deadline)
    ready_utc = ensure_utc(task.ready_at) or now_utc

    # 1. Travel from driver's current location to donor pickup
    driver_to_pickup_m = haversine_distance_m(
        driver.lat, driver.lng, task.pickup_lat, task.pickup_lng
    )
    pickup_travel_s = estimate_travel_duration_s(
        distance_m=driver_to_pickup_m,
        vehicle_type=driver.vehicle_type,
        dt=now_utc,
        speed_factor_ewma=driver.speed_factor_ewma,
    )
    pickup_eta_min = pickup_travel_s / 60.0
    driver_arrives_pickup = now_utc + timedelta(seconds=pickup_travel_s)

    # Cannot pickup before ready_at
    actual_pickup_start = max(driver_arrives_pickup, ready_utc)
    pickup_complete = actual_pickup_start + timedelta(seconds=DWELL_TIME_PICKUP_S)

    # 2. Travel from donor pickup to recipient dropoff
    pickup_to_dropoff_m = haversine_distance_m(
        task.pickup_lat, task.pickup_lng, task.dropoff_lat, task.dropoff_lng
    )
    delivery_travel_s = estimate_travel_duration_s(
        distance_m=pickup_to_dropoff_m,
        vehicle_type=driver.vehicle_type,
        dt=pickup_complete,
        speed_factor_ewma=driver.speed_factor_ewma,
    )
    predicted_delivery = pickup_complete + timedelta(
        seconds=delivery_travel_s + DWELL_TIME_DROPOFF_S
    )

    # Hard feasibility check: R4 strict delivery before safe-until deadline
    if predicted_delivery > deadline_utc:
        return INFEASIBLE_COST, pickup_eta_min, predicted_delivery

    # Soft deadline = deadline - 10% of window
    window_s = max(60.0, (deadline_utc - ready_utc).total_seconds())
    soft_deadline = deadline_utc - timedelta(seconds=0.10 * window_s)
    late_seconds = max(0.0, (predicted_delivery - soft_deadline).total_seconds())
    late_minutes = late_seconds / 60.0

    # Weights from spec
    w_pick = 1.0
    w_late = 8.0
    w_acc = 0.6
    w_load = 0.3
    w_risk = -2.0 if task.risk == Risk.CRITICAL else 0.0

    p_accept = max(0.1, min(1.0, driver.accept_rate_ewma))
    acc_term = (1.0 - p_accept) * 10.0
    load_term = float(driver.deliveries_last_2h)

    cost = (
        w_pick * pickup_eta_min
        + w_late * late_minutes
        + w_acc * acc_term
        + w_load * load_term
        + w_risk
    )

    return max(0.0, cost), pickup_eta_min, predicted_delivery


def solve_bipartite_assignment(
    tasks: list[DispatchTask],
    drivers: list[DriverCandidate],
    now: datetime,
) -> list[AssignmentResult]:
    """
    Stage 2: Solve min-cost bipartite assignment for idle drivers using SciPy.
    """
    idle_drivers = [d for d in drivers if d.status == DriverStatus.AVAILABLE]
    if not tasks or not idle_drivers:
        return []

    num_drivers = len(idle_drivers)
    num_tasks = len(tasks)

    cost_matrix = np.full((num_drivers, num_tasks), INFEASIBLE_COST, dtype=float)
    eta_matrix = np.zeros((num_drivers, num_tasks), dtype=float)
    delivery_map: dict[tuple[int, int], datetime] = {}

    for i, d in enumerate(idle_drivers):
        for j, t in enumerate(tasks):
            # Check cold and capacity first
            if t.storage == StorageCondition.COLD and not d.has_cold_box:
                continue
            if t.portions > d.capacity_portions:
                continue

            cost, eta_min, pred_deliv = compute_driver_task_cost(d, t, now)
            cost_matrix[i, j] = cost
            eta_matrix[i, j] = eta_min
            delivery_map[(i, j)] = pred_deliv

    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    results: list[AssignmentResult] = []
    for r, c in zip(row_ind, col_ind, strict=False):
        cost = cost_matrix[r, c]
        if cost < INFEASIBLE_COST:
            d = idle_drivers[r]
            t = tasks[c]
            results.append(
                AssignmentResult(
                    driver_id=d.id,
                    task_id=t.allocation_id,
                    cost_minutes=round(cost, 2),
                    pickup_eta_min=round(eta_matrix[r, c], 2),
                    predicted_delivery=delivery_map[(r, c)],
                    is_stacked=False,
                )
            )

    return results
