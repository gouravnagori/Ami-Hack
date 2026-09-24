import uuid
from datetime import datetime

from app.core.config import DriverStatus, VehicleType
from app.schemas.common import SchemaBase


class DriverShiftRequest(SchemaBase):
    status: DriverStatus


class DriverProfileUpdateRequest(SchemaBase):
    vehicle_type: VehicleType | None = None
    capacity_portions: int | None = None
    has_cold_box: bool | None = None
    service_radius_m: float | None = None


class DriverLocationPing(SchemaBase):
    lat: float
    lng: float
    speed: float | None = None
    heading: float | None = None
    ts: datetime | None = None


class DriverProfileSchema(SchemaBase):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    phone: str
    vehicle_type: VehicleType
    capacity_portions: int
    has_cold_box: bool
    status: DriverStatus
    lat: float | None = None
    lng: float | None = None
    last_ping_at: datetime | None = None
    accept_rate_ewma: float
    speed_factor_ewma: float
    service_radius_m: float


class DriverStatsSchema(SchemaBase):
    completed_deliveries: int
    total_meals_delivered: int
    total_co2e_saved_kg: float
    on_time_rate: float
    total_distance_km: float
    hours_online: float


class DriverHistoryItem(SchemaBase):
    route_id: uuid.UUID
    completed_at: datetime
    stops_count: int
    total_portions: int
    distance_m: float
    duration_s: float
