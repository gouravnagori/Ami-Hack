"""
Travel-time and ETA Service.

Implements:
- Vehicle-specific base speeds (bicycle 12, scooter 24, e_rickshaw 20, van 22 km/h)
- 1.35 detour factor for road distance approximation from haversine
- Seeded traffic factor table by hour & weekday
- EWMA online learning for driver speed factor (0.8*old + 0.2*(actual/planned))
- Standard dwell times (180s pickup, 180s dropoff)
"""

from datetime import UTC, datetime

from app.core.config import VehicleType, settings

# Vehicle base speeds in km/h
VEHICLE_SPEEDS_KMH: dict[VehicleType, float] = {
    VehicleType.BICYCLE: 12.0,
    VehicleType.SCOOTER: 24.0,
    VehicleType.E_RICKSHAW: 20.0,
    VehicleType.VAN: 22.0,
}

DWELL_TIME_PICKUP_S: float = 180.0  # 3 minutes
DWELL_TIME_DROPOFF_S: float = 180.0  # 3 minutes
ROAD_DETOUR_FACTOR: float = 1.35


def get_traffic_factor(dt: datetime | None = None) -> float:
    """Return traffic multiplier based on hour of day and weekday."""
    if dt is None:
        dt = datetime.now(UTC)

    hour = dt.hour
    is_weekend = dt.weekday() >= 5

    if is_weekend:
        if 12 <= hour < 16:
            factor = 1.20
        elif 18 <= hour < 22:
            factor = 1.25
        else:
            factor = 1.05
    else:
        # Weekday
        if 8 <= hour < 11:
            factor = 1.35  # Morning peak
        elif 12 <= hour < 15:
            factor = 1.20  # Lunch hour
        elif 17 <= hour < 21:
            factor = 1.45  # Evening peak
        elif 21 <= hour < 23:
            factor = 1.15
        else:
            factor = 1.05  # Late night / early morning

    if getattr(settings, "CHAOS_TRAFFIC_SPIKE", False):
        factor *= 1.8

    return factor


def update_speed_factor_ewma(
    current_ewma: float,
    actual_duration_s: float,
    planned_duration_s: float,
) -> float:
    """
    Update driver's speed factor EWMA:
    speed_factor_ewma = 0.8 * old + 0.2 * (actual / planned)
    Clipped between 0.5 (fast driver) and 2.5 (slow/delayed driver).
    """
    if planned_duration_s <= 0.0:
        return current_ewma
    ratio = actual_duration_s / planned_duration_s
    new_ewma = 0.8 * current_ewma + 0.2 * ratio
    return max(0.5, min(2.5, new_ewma))


def estimate_travel_duration_s(
    distance_m: float,
    vehicle_type: VehicleType = VehicleType.SCOOTER,
    dt: datetime | None = None,
    speed_factor_ewma: float = 1.0,
) -> float:
    """
    Estimate travel duration in seconds given distance, vehicle type, and current time.
    """
    speed_kmh = VEHICLE_SPEEDS_KMH.get(vehicle_type, 24.0)
    speed_m_s = (speed_kmh * 1000.0) / 3600.0
    base_seconds = distance_m / max(0.1, speed_m_s)
    traffic = get_traffic_factor(dt)
    return base_seconds * traffic * speed_factor_ewma


def classify_risk(slack_s: float, window_s: float) -> str:
    """
    Classify SLA risk level based on remaining slack and total window duration.
    Ratio = slack_s / max(1.0, window_s)
    - safe: slack ratio > 0.30
    - tight: slack ratio between 0.10 and 0.30
    - critical: slack ratio < 0.10
    """
    ratio = slack_s / max(1.0, window_s)
    if ratio > 0.30:
        return "safe"
    elif ratio >= 0.10:
        return "tight"
    return "critical"

