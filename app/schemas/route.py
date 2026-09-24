import uuid
from datetime import datetime

from pydantic import Field

from app.core.config import DietType, Risk, StopStatus, StopType, StorageCondition
from app.schemas.common import GeoPoint, SchemaBase


class StopPlace(GeoPoint):
    name: str


class StopWindow(SchemaBase):
    start: datetime
    end: datetime


class StopSchema(SchemaBase):
    id: uuid.UUID
    seq: int
    type: StopType
    allocation_id: uuid.UUID
    place: StopPlace
    window: StopWindow
    planned_arrival: datetime
    predicted_arrival: datetime
    slack_seconds: float
    risk: Risk
    portions: int
    diet: DietType
    storage: StorageCondition
    container_label: str
    status: StopStatus
    requires_otp: bool


class RouteSchema(SchemaBase):
    id: uuid.UUID
    driver_id: uuid.UUID
    version: int
    status: str
    stops: list[StopSchema] = Field(default_factory=list)
    polyline: list[list[float]] = Field(default_factory=list)  # [lng, lat]
    total_distance_m: float
    total_duration_s: float
    replanned_reason: str | None = None
    saved_seconds_vs_previous: float | None = None


class StopCompleteRequest(SchemaBase):
    otp: str | None = None
    photo_base64: str | None = None
    temp_c: float | None = None


class StopIssueRequest(SchemaBase):
    code: str
    note: str | None = None

