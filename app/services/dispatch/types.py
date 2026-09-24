"""
Data types and specifications for dispatch engine.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.core.config import DietType, DriverStatus, Risk, StopType, StorageCondition, VehicleType


@dataclass(frozen=True)
class DispatchTask:
    """A delivery task representing one allocation from pickup to dropoff."""

    allocation_id: uuid.UUID
    donation_id: uuid.UUID
    portions: int
    diet: DietType
    storage: StorageCondition
    container_label: str
    deadline: datetime
    # Pickup details
    pickup_lat: float
    pickup_lng: float
    pickup_address: str
    pickup_name: str
    ready_at: datetime
    latest_pickup: datetime
    # Dropoff details
    dropoff_lat: float
    dropoff_lng: float
    dropoff_address: str
    dropoff_name: str
    dropoff_window_end: datetime
    # Slack and risk
    slack_seconds: float = 0.0
    slack_ratio: float = 1.0
    risk: Risk = Risk.SAFE


@dataclass
class DriverCandidate:
    """Driver snapshot used for dispatch assignment and routing."""

    id: uuid.UUID
    user_id: uuid.UUID
    vehicle_type: VehicleType
    capacity_portions: int
    has_cold_box: bool
    status: DriverStatus
    lat: float
    lng: float
    last_ping_at: datetime | None = None
    accept_rate_ewma: float = 0.90
    speed_factor_ewma: float = 1.0
    service_radius_m: float = 10000.0
    deliveries_last_2h: int = 0
    active_route_id: uuid.UUID | None = None
    current_load_portions: int = 0
    existing_stops: list["StopPlan"] = field(default_factory=list)


@dataclass
class StopPlan:
    """Planned stop in a route sequence."""

    id: uuid.UUID | None = None
    seq: int = 0
    type: StopType = StopType.PICKUP
    allocation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    lat: float = 0.0
    lng: float = 0.0
    name: str = ""
    address: str = ""
    window_start: datetime = field(default_factory=datetime.utcnow)
    window_end: datetime = field(default_factory=datetime.utcnow)
    planned_arrival: datetime = field(default_factory=datetime.utcnow)
    predicted_arrival: datetime = field(default_factory=datetime.utcnow)
    slack_seconds: float = 0.0
    portions: int = 0
    diet: DietType = DietType.VEG
    storage: StorageCondition = StorageCondition.AMBIENT
    container_label: str = "Container A"
    requires_otp: bool = True


@dataclass
class AssignmentResult:
    """Outcome of Stage 2 idle driver assignment."""

    driver_id: uuid.UUID
    task_id: uuid.UUID
    cost_minutes: float
    pickup_eta_min: float
    predicted_delivery: datetime
    is_stacked: bool = False


@dataclass
class InsertionResult:
    """Outcome of Stage 3 stacked route insertion."""

    driver_id: uuid.UUID
    task_id: uuid.UUID
    pickup_index: int
    dropoff_index: int
    added_detour_s: float
    cost_minutes: float
    new_stops: list[StopPlan]
