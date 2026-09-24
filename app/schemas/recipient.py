import uuid
from datetime import date, datetime, time

from pydantic import Field

from app.core.config import DietType, StorageCondition
from app.schemas.common import GeoPoint, SchemaBase


class ColdCapacity(SchemaBase):
    max: int
    used: int


class ProjectionPoint(SchemaBase):
    at: datetime
    available: int


class AcceptsSummary(SchemaBase):
    diets: list[DietType]
    storage: list[StorageCondition]


class CapacitySnapshot(SchemaBase):
    org_id: uuid.UUID
    as_of: datetime
    max_portions: int
    in_stock_portions: int
    service_rate_per_hour: float
    held_portions: int
    committed_portions: int
    cold: ColdCapacity
    available_now: int
    projection: list[ProjectionPoint] = Field(default_factory=list)
    accepts: AcceptsSummary
    is_open: bool
    closes_at: datetime | None = None


class CapacityAdjustRequest(SchemaBase):
    delta_portions: int
    reason: str


class CapacityFullRequest(SchemaBase):
    is_full: bool = True


class CapacityWindowItem(SchemaBase):
    dow: int | None = None
    specific_date: date | None = None
    start_time: time
    end_time: time
    max_portions: int


class CapacityWindowsUpdateRequest(SchemaBase):
    windows: list[CapacityWindowItem]


class RecipientProfileSchema(SchemaBase):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    address: str
    geo: GeoPoint
    fssai_reg_no: str | None = None
    verified_at: datetime | None = None
    accepts_diets: list[DietType]
    accepts_storage: list[StorageCondition]
    cold_max_units: int
    service_rate_per_hour: float
    need_level: float
    is_open_override: bool | None = None
    reliability_ewma: float


class RecipientProfileUpdate(SchemaBase):
    name: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    fssai_reg_no: str | None = None
    accepts_diets: list[DietType] | None = None
    accepts_storage: list[StorageCondition] | None = None
    cold_max_units: int | None = None
    service_rate_per_hour: float | None = None
    need_level: float | None = None


class IncomingAllocationItem(SchemaBase):
    allocation_id: uuid.UUID
    donation_id: uuid.UUID
    portions: int
    diet: DietType
    storage: StorageCondition
    status: str
    container_label: str
    deadline: datetime
    predicted_delivery: datetime | None = None
    slack_seconds: float | None = None
    risk: str
    driver_id: uuid.UUID | None = None
    driver_name: str | None = None
    driver_phone: str | None = None
    driver_vehicle: str | None = None
    donor_name: str
    items: list[str] = Field(default_factory=list)


class ConfirmDeliveryRequest(SchemaBase):
    otp: str
    received_portions: int
    photo_base64: str | None = None
    temp_c: float | None = None


class ConfirmDeliveryResponse(SchemaBase):
    status: str
    allocation_id: uuid.UUID
    received_portions: int
    confirmed_at: datetime

