import uuid
from datetime import datetime

from pydantic import Field

from app.core.config import DietType, DonationStatus, Risk, StorageCondition, VehicleType
from app.schemas.common import GeoPoint, SchemaBase


class DonationItemSchema(SchemaBase):
    name: str
    portions: int = Field(..., gt=0)
    weight_kg: float | None = None


class TimeWindow(SchemaBase):
    start: datetime
    end: datetime


class DriverSummary(SchemaBase):
    id: uuid.UUID
    name: str
    vehicle: VehicleType
    phone_masked: str


class AllocationRecipientSummary(SchemaBase):
    id: uuid.UUID
    name: str
    geo: GeoPoint


class MatchReason(SchemaBase):
    code: str
    label: str
    weight: float


class MatchExplanation(SchemaBase):
    score: float
    reasons: list[MatchReason]


class AllocationSchema(SchemaBase):
    id: uuid.UUID
    donation_id: uuid.UUID
    portions: int
    status: str
    recipient: AllocationRecipientSummary
    container_label: str
    deadline: datetime
    predicted_delivery: datetime | None = None
    slack_seconds: float | None = None
    risk: Risk
    match_explanation: MatchExplanation | None = None
    driver: DriverSummary | None = None
    pickup_otp: str | None = None


class DonationSchema(SchemaBase):
    id: uuid.UUID
    donor_id: uuid.UUID
    status: DonationStatus
    items: list[DonationItemSchema]
    total_portions: int
    diet: DietType
    storage: StorageCondition
    prepared_at: datetime
    safe_until: datetime
    pickup_window: TimeWindow
    pickup: GeoPoint
    photo_url: str | None = None
    notes: str | None = None
    parse_confidence: float | None = None
    allocations: list[AllocationSchema] = Field(default_factory=list)
    risk: Risk
    slack_seconds: float
    created_at: datetime


class DonationCreateRequest(SchemaBase):
    items: list[DonationItemSchema]
    diet: DietType
    storage: StorageCondition
    category: str = "cooked_meals"
    prepared_at: datetime
    best_before: datetime | None = None
    safe_until: datetime | None = None  # Server may cap this
    pickup_window: TimeWindow
    pickup: GeoPoint
    photo_url: str | None = None
    notes: str | None = None


class DonationPreviewBestOrg(SchemaBase):
    id: uuid.UUID
    name: str
    distance_m: float
    score: float
    reasons: list[MatchReason] = Field(default_factory=list)


class DonationPreviewResponse(SchemaBase):
    feasible_recipients: int
    best: DonationPreviewBestOrg | None = None
    warnings: list[str] = Field(default_factory=list)


class DonationListResponse(SchemaBase):
    items: list[DonationSchema]
    next_cursor: str | None = None


class DonationParseRequest(SchemaBase):
    text: str | None = None
    photo_base64: str | None = None


class DonationParseResponse(SchemaBase):
    draft: dict | None = None
    confidence: float = 0.0
    missing: list[str] = Field(default_factory=list)

