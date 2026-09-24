import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin, utc_now


class AuditEvent(Base, UUIDPrimaryKeyMixin):
    """
    Append-only audit trail recording every state change and operational event.
    """

    __tablename__ = "audit_events"

    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True, nullable=False
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True, index=True
    )
    entity: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # donation, allocation, offer, route
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # created, updated, accepted, delivered, cancelled
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    __table_args__ = (Index("ix_audit_events_entity_lookup", "entity", "entity_id"),)
