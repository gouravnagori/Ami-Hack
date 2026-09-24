import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import DietType, DonationStatus, StorageCondition
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.allocation import Allocation
    from app.db.models.donor import Donor


class Donation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "donations"

    donor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("donors.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[DonationStatus] = mapped_column(
        Enum(DonationStatus, native_enum=False, length=30),
        default=DonationStatus.DRAFT,
        nullable=False,
        index=True,
    )
    diet: Mapped[DietType] = mapped_column(
        Enum(DietType, native_enum=False, length=20),
        nullable=False,
    )
    storage: Mapped[StorageCondition] = mapped_column(
        Enum(StorageCondition, native_enum=False, length=20),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(50), default="cooked_meals", nullable=False)
    total_portions: Mapped[int] = mapped_column(Integer, nullable=False)

    # Time parameters
    prepared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    best_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    safe_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pickup_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pickup_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Geo parameters
    pickup_lat: Mapped[float] = mapped_column(Float, nullable=False)
    pickup_lng: Mapped[float] = mapped_column(Float, nullable=False)
    pickup_address: Mapped[str] = mapped_column(String(500), nullable=False)

    # Media & AI
    photo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    parse_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    donor: Mapped["Donor"] = relationship("Donor", back_populates="donations")
    items: Mapped[list["DonationItem"]] = relationship(
        "DonationItem", back_populates="donation", cascade="all, delete-orphan"
    )
    allocations: Mapped[list["Allocation"]] = relationship(
        "Allocation", back_populates="donation", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_donations_active_status", "status"),)


class DonationItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "donation_items"

    donation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("donations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    portions: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)

    donation: Mapped["Donation"] = relationship("Donation", back_populates="items")
