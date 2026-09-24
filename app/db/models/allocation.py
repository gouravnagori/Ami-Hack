import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import AllocationStatus
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.capacity import CapacityReservation
    from app.db.models.donation import Donation
    from app.db.models.driver import Driver
    from app.db.models.offer import Offer
    from app.db.models.recipient import RecipientOrg
    from app.db.models.route import RouteStop


class Allocation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "allocations"

    donation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("donations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recipient_orgs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    portions: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[AllocationStatus] = mapped_column(
        Enum(AllocationStatus, native_enum=False, length=30),
        default=AllocationStatus.OFFERED,
        nullable=False,
        index=True,
    )
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    container_label: Mapped[str] = mapped_column(String(50), default="Container A", nullable=False)

    predicted_delivery: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    slack_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Verification OTPs (stored hashed)
    pickup_otp_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dropoff_otp_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Assigned driver
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("drivers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    donation: Mapped["Donation"] = relationship("Donation", back_populates="allocations")
    recipient: Mapped["RecipientOrg"] = relationship("RecipientOrg", back_populates="allocations")
    reservations: Mapped[list["CapacityReservation"]] = relationship(
        "CapacityReservation", back_populates="allocation"
    )
    offers: Mapped[list["Offer"]] = relationship("Offer", back_populates="allocation")
    stops: Mapped[list["RouteStop"]] = relationship("RouteStop", back_populates="allocation")
    driver: Mapped["Driver | None"] = relationship("Driver")
