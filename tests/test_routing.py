"""
Unit tests for Routing, ETA model, and OSRM fallback.
"""

from datetime import UTC, datetime

import pytest

from app.core.config import VehicleType
from app.services.routing.client import RoutingClient
from app.services.routing.eta import (
    estimate_travel_duration_s,
    get_traffic_factor,
    update_speed_factor_ewma,
)


def test_traffic_factor_peaks():
    # Morning peak: 9 AM weekday
    morning_peak = datetime(2026, 9, 23, 9, 30, tzinfo=UTC)  # Wednesday
    tf_morning = get_traffic_factor(morning_peak)
    assert tf_morning >= 1.35

    # Evening peak: 6 PM weekday
    evening_peak = datetime(2026, 9, 23, 18, 0, tzinfo=UTC)  # Wednesday
    tf_evening = get_traffic_factor(evening_peak)
    assert tf_evening >= 1.40

    # Late night: 2 AM
    night = datetime(2026, 9, 23, 2, 0, tzinfo=UTC)
    tf_night = get_traffic_factor(night)
    assert tf_night < 1.15


def test_speed_factor_ewma_learning():
    # Slower than planned: actual 600s, planned 300s -> ratio 2.0
    # 0.8 * 1.0 + 0.2 * 2.0 = 1.2
    new_ewma = update_speed_factor_ewma(1.0, actual_duration_s=600.0, planned_duration_s=300.0)
    assert pytest.approx(new_ewma, 0.01) == 1.2

    # Faster than planned: actual 200s, planned 400s -> ratio 0.5
    # 0.8 * 1.2 + 0.2 * 0.5 = 0.96 + 0.10 = 1.06
    new_ewma_2 = update_speed_factor_ewma(new_ewma, actual_duration_s=200.0, planned_duration_s=400.0)
    assert pytest.approx(new_ewma_2, 0.01) == 1.06


def test_vehicle_travel_duration_comparison():
    dist_m = 5000.0  # 5 km
    now = datetime(2026, 9, 23, 14, 0, tzinfo=UTC)

    t_bike = estimate_travel_duration_s(dist_m, VehicleType.BICYCLE, now)
    t_scooter = estimate_travel_duration_s(dist_m, VehicleType.SCOOTER, now)

    # Scooter is 24 km/h, bike is 12 km/h -> bike takes twice as long
    assert t_bike > t_scooter
    assert pytest.approx(t_bike / t_scooter, 0.05) == 2.0


@pytest.mark.asyncio
async def test_osrm_fallback_haversine():
    client = RoutingClient(osrm_url="http://non-existent-osrm:9999")
    coords = [
        (28.6139, 77.2090),  # Connaught Place
        (28.5355, 77.3910),  # Noida
    ]

    dist_mat, dur_mat = await client.get_table(coords, VehicleType.SCOOTER)
    assert len(dist_mat) == 2
    assert len(dist_mat[0]) == 2
    assert dist_mat[0][0] == 0.0
    assert dist_mat[0][1] > 10000.0  # ~18-22 km road distance
    assert dur_mat[0][1] > 0.0

    total_dist, total_dur, polyline = await client.get_route(coords, VehicleType.SCOOTER)
    assert total_dist > 10000.0
    assert total_dur > 0.0
    assert len(polyline) == 2
