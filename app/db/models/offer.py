import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import OfferKind, OfferStatus
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.allocation import Allocation
    from app.db.models.user import User


class Offer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "offers"

    kind: Mapped[OfferKind] = mapped_column(
        Enum(OfferKind, native_enum=False, length=20),
        nullable=False,
    )
    allocation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("allocations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    route_preview: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    target_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus, native_enum=False, length=20),
        default=OfferStatus.PENDING,
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    allocation: Mapped["Allocation | None"] = relationship("Allocation", back_populates="offers")
    target_user: Mapped["User"] = relationship("User")

    __table_args__ = (Index("ix_offers_pending_expiry", "expires_at", "status"),)
