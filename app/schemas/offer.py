import uuid
from datetime import datetime

from pydantic import Field

from app.core.config import DietType, OfferKind, OfferStatus, StorageCondition
from app.schemas.common import SchemaBase
from app.schemas.donation import MatchExplanation


class OfferDonationSummary(SchemaBase):
    id: uuid.UUID
    donor_name: str
    diet: DietType
    storage: StorageCondition
    total_portions: int
    safe_until: datetime
    distance_m: float
    items: list[str] = Field(default_factory=list)


class OfferSchema(SchemaBase):
    id: uuid.UUID
    kind: OfferKind
    status: OfferStatus
    created_at: datetime
    expires_at: datetime
    donation: OfferDonationSummary

    # kind = recipient
    max_acceptable_portions: int | None = None
    offered_portions: int | None = None
    match_explanation: MatchExplanation | None = None

    # kind = driver
    route_preview: dict | None = None


class OfferAcceptRequest(SchemaBase):
    portions: int | None = None


class OfferDeclineRequest(SchemaBase):
    reason_code: str = "other"
    reason: str | None = None
