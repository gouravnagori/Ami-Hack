import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.allocation import Allocation
    from app.db.models.capacity import CapacityAdjustment, CapacityReservation, CapacityWindow
    from app.db.models.user import User


class RecipientOrg(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "recipient_orgs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    lng: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    fssai_reg_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    max_capacity_portions: Mapped[int] = mapped_column(Integer, default=150, nullable=False)
    food_restrictions: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receiving_hours: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Dietary & storage constraints
    accepts_diets: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )  # ["veg", "egg", "non_veg"]
    accepts_storage: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )  # ["ambient", "hot", "cold"]
    cold_max_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Operational metrics
    service_rate_per_hour: Mapped[float] = mapped_column(
        Float, default=20.0, nullable=False
    )  # portions served per hour
    need_level: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)  # 0.0 to 1.0
    is_open_override: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reliability_ewma: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="recipient_profile")
    capacity_windows: Mapped[list["CapacityWindow"]] = relationship(
        "CapacityWindow", back_populates="org", cascade="all, delete-orphan"
    )
    capacity_adjustments: Mapped[list["CapacityAdjustment"]] = relationship(
        "CapacityAdjustment", back_populates="org", cascade="all, delete-orphan"
    )
    capacity_reservations: Mapped[list["CapacityReservation"]] = relationship(
        "CapacityReservation", back_populates="org", cascade="all, delete-orphan"
    )
    allocations: Mapped[list["Allocation"]] = relationship("Allocation", back_populates="recipient")
