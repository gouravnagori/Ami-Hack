"""
Stage 4: PDPTW (Pickup and Delivery with Time Windows) Route Optimisation.

Uses Google OR-Tools Routing Library:
- Start at driver's current coordinates
- Pickup and Delivery pairs with precedence constraint (pickup before dropoff)
- Capacity dimension (+portions at pickup, -portions at dropoff)
- Time dimension with time windows [window_start, window_end] and service dwell times
- Disjunction penalties for graceful shedding
- Guided Local Search with 2-second time limit
- Graceful 2-opt fallback when solver times out or finds no feasible route
"""

from datetime import UTC, datetime, timedelta

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from app.core.config import StopType
from app.core.logging import get_logger
from app.services.capacity import ensure_utc
from app.services.dispatch.types import DriverCandidate, StopPlan
from app.services.matching import haversine_distance_m
from app.services.routing.eta import (
    DWELL_TIME_DROPOFF_S,
    DWELL_TIME_PICKUP_S,
    ROAD_DETOUR_FACTOR,
    estimate_travel_duration_s,
)

logger = get_logger(__name__)


def compute_sequence_duration_s(
    start_lat: float,
    start_lng: float,
    stops: list[StopPlan],
    driver: DriverCandidate,
    now: datetime,
) -> float:
    """Calculate total duration of stop sequence including travel and dwell times."""
    curr_lat, curr_lng = start_lat, start_lng
    curr_time = ensure_utc(now) or datetime.now(UTC)
    total_s = 0.0

    for s in stops:
        dist_m = haversine_distance_m(curr_lat, curr_lng, s.lat, s.lng) * ROAD_DETOUR_FACTOR
        leg_s = estimate_travel_duration_s(dist_m, driver.vehicle_type, curr_time, driver.speed_factor_ewma)
        total_s += leg_s
        dwell = DWELL_TIME_PICKUP_S if s.type == StopType.PICKUP else DWELL_TIME_DROPOFF_S
        total_s += dwell
        curr_time += timedelta(seconds=leg_s + dwell)
        curr_lat, curr_lng = s.lat, s.lng

    return total_s


def solve_pdptw_ortools(
    driver: DriverCandidate,
    stops: list[StopPlan],
    now: datetime,
    time_limit_s: float = 2.0,
) -> tuple[list[StopPlan], float] | None:
    """
    Build and solve OR-Tools PDPTW model for a driver's route.
    Returns (optimized_stops, total_duration_s) or None if infeasible.
    """
    n_stops = len(stops)
    if n_stops < 2:
        return stops, 0.0

    now_utc = ensure_utc(now) or datetime.now(UTC)

    # Node 0: Driver start location
    # Node 1 .. n_stops: Stops
    # Node n_stops + 1: Open route dummy depot (end node)
    locations = [(driver.lat, driver.lng)] + [(s.lat, s.lng) for s in stops]
    n_nodes = len(locations)

    # Precompute travel time matrix (in integer seconds)
    travel_times: list[list[int]] = [[0] * n_nodes for _ in range(n_nodes)]
    for i in range(n_nodes):
        for j in range(n_nodes):
            if i == j:
                continue
            lat1, lng1 = locations[i]
            lat2, lng2 = locations[j]
            d_m = haversine_distance_m(lat1, lng1, lat2, lng2) * ROAD_DETOUR_FACTOR
            t_s = estimate_travel_duration_s(d_m, driver.vehicle_type, now_utc, driver.speed_factor_ewma)
            dwell = 0.0
            if j > 0 and j <= n_stops:
                dwell = DWELL_TIME_PICKUP_S if stops[j - 1].type == StopType.PICKUP else DWELL_TIME_DROPOFF_S
            travel_times[i][j] = int(t_s + dwell)

    manager = pywrapcp.RoutingIndexManager(n_nodes, 1, [0], [0])
    routing = pywrapcp.RoutingModel(manager)

    # Transit callback
    def time_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return travel_times[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # 1. Capacity dimension
    demands: list[int] = [0] * n_nodes
    for idx, s in enumerate(stops):
        node = idx + 1
        demands[node] = s.portions if s.type == StopType.PICKUP else -s.portions

    def demand_callback(from_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        [driver.capacity_portions],  # vehicle capacities
        True,  # start cumul to zero
        "Capacity",
    )

    # 2. Time dimension
    routing.AddDimension(
        transit_callback_index,
        3600,  # 1 hour slack for waiting at windows
        86400,  # 24 hours max route duration
        False,  # Don't force start cumul to zero
        "Time",
    )
    time_dimension = routing.GetDimensionOrDie("Time")

    # Set time windows
    for idx, s in enumerate(stops):
        node = idx + 1
        index = manager.NodeToIndex(node)
        w_start = ensure_utc(s.window_start) or now_utc
        w_end = ensure_utc(s.window_end) or (now_utc + timedelta(hours=4))
        start_sec = max(0, int((w_start - now_utc).total_seconds()))
        end_sec = max(start_sec + 60, int((w_end - now_utc).total_seconds()))
        time_dimension.CumulVar(index).SetRange(start_sec, end_sec)

    # 3. Pickup and Delivery Pairs
    # Group stops by allocation_id
    alloc_pairs: dict[str, dict[StopType, int]] = {}
    for idx, s in enumerate(stops):
        key = str(s.allocation_id)
        if key not in alloc_pairs:
            alloc_pairs[key] = {}
        alloc_pairs[key][s.type] = idx + 1

    for pair in alloc_pairs.values():
        if StopType.PICKUP in pair and StopType.DROPOFF in pair:
            p_node = pair[StopType.PICKUP]
            d_node = pair[StopType.DROPOFF]
            p_idx = manager.NodeToIndex(p_node)
            d_idx = manager.NodeToIndex(d_node)
            routing.AddPickupAndDelivery(p_idx, d_idx)
            routing.solver().Add(routing.VehicleVar(p_idx) == routing.VehicleVar(d_idx))
            routing.solver().Add(time_dimension.CumulVar(p_idx) <= time_dimension.CumulVar(d_idx))
            # Disjunction penalty for optional shedding
            routing.AddDisjunction([p_idx, d_idx], 100000)

    # Search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = max(1, int(time_limit_s))

    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        return None

    # Extract ordered stops
    index = routing.Start(0)
    ordered_stop_indices: list[int] = []
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        if node > 0:
            ordered_stop_indices.append(node - 1)
        index = solution.Value(routing.NextVar(index))

    # All stops must be served
    if len(ordered_stop_indices) != n_stops:
        return None

    ordered_stops = [stops[i] for i in ordered_stop_indices]
    for seq_num, s in enumerate(ordered_stops, start=1):
        s.seq = seq_num

    total_duration_s = float(solution.ObjectiveValue())
    return ordered_stops, total_duration_s


def fallback_2opt_pass(
    start_lat: float,
    start_lng: float,
    stops: list[StopPlan],
    driver: DriverCandidate,
    now: datetime,
) -> list[StopPlan]:
    """
    Greedy 2-opt pass on existing stop plan, respecting precedence (p before d).
    """
    n = len(stops)
    if n <= 2:
        return list(stops)

    best_stops = list(stops)
    best_duration = compute_sequence_duration_s(start_lat, start_lng, best_stops, driver, now)

    improved = True
    iterations = 0
    while improved and iterations < 10:
        improved = False
        iterations += 1
        for i in range(n - 1):
            for j in range(i + 1, n):
                # Try reversing subsegment between i and j
                cand = best_stops[:i] + list(reversed(best_stops[i : j + 1])) + best_stops[j + 1 :]
                # Check precedence: pickup before dropoff for each allocation
                pos_map: dict[str, dict[StopType, int]] = {}
                valid = True
                for idx, s in enumerate(cand):
                    k = str(s.allocation_id)
                    if k not in pos_map:
                        pos_map[k] = {}
                    pos_map[k][s.type] = idx

                for _k, p_dict in pos_map.items():
                    if StopType.PICKUP in p_dict and StopType.DROPOFF in p_dict:
                        if p_dict[StopType.PICKUP] > p_dict[StopType.DROPOFF]:
                            valid = False
                            break

                if not valid:
                    continue

                dur = compute_sequence_duration_s(start_lat, start_lng, cand, driver, now)
                if dur < best_duration - 1.0:
                    best_duration = dur
                    best_stops = cand
                    improved = True

    for i, s in enumerate(best_stops, start=1):
        s.seq = i

    return best_stops


def optimize_route_pdptw(
    driver: DriverCandidate,
    stops: list[StopPlan],
    now: datetime,
    time_limit_s: float = 2.0,
) -> tuple[list[StopPlan], float, str]:
    """
    Entry point for Route Optimisation:
    Attempts OR-Tools PDPTW solver. If unavailable, timed out, or infeasible,
    falls back to a fast 2-opt improvement pass.
    Returns: (optimized_stops, saved_seconds, replanned_reason)
    """
    if len(stops) <= 2:
        return stops, 0.0, "none_needed"

    original_duration = compute_sequence_duration_s(
        driver.lat, driver.lng, stops, driver, now
    )

    try:
        ortools_result = solve_pdptw_ortools(driver, stops, now, time_limit_s)
        if ortools_result:
            opt_stops, _ = ortools_result
            new_dur = compute_sequence_duration_s(
                driver.lat, driver.lng, opt_stops, driver, now
            )
            saved = max(0.0, original_duration - new_dur)
            return opt_stops, round(saved, 1), "pdptw_or_tools"
    except Exception as e:
        logger.warning("ortools_pdptw_error_falling_back", error=str(e))

    # Fallback to 2-opt
    opt_stops = fallback_2opt_pass(driver.lat, driver.lng, stops, driver, now)
    new_dur = compute_sequence_duration_s(
        driver.lat, driver.lng, opt_stops, driver, now
    )
    saved = max(0.0, original_duration - new_dur)
    return opt_stops, round(saved, 1), "fallback_2opt"
