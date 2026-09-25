import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import DriverStatus, VehicleType
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.db.models.route import Route
    from app.db.models.user import User


class Driver(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "drivers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    vehicle_type: Mapped[VehicleType] = mapped_column(
        Enum(VehicleType, native_enum=False, length=20),
        default=VehicleType.SCOOTER,
        nullable=False,
    )
    vehicle_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    operating_area: Mapped[str | None] = mapped_column(String(255), nullable=True)
    capacity_portions: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    has_cold_box: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[DriverStatus] = mapped_column(
        Enum(DriverStatus, native_enum=False, length=20),
        default=DriverStatus.OFFLINE,
        nullable=False,
        index=True,
    )

    # Live telematics
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_ping_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Learning & EWMA parameters
    accept_rate_ewma: Mapped[float] = mapped_column(Float, default=0.90, nullable=False)
    speed_factor_ewma: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    service_radius_m: Mapped[float] = mapped_column(Float, default=10000.0, nullable=False)  # 10 km
    shift_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="driver_profile")
    routes: Mapped[list["Route"]] = relationship("Route", back_populates="driver")
    locations: Mapped[list["DriverLocation"]] = relationship(
        "DriverLocation", back_populates="driver", cascade="all, delete-orphan"
    )


class DriverLocation(Base, UUIDPrimaryKeyMixin):
    """Historical telematics stream (partitioned or pruned after 48h)."""

    __tablename__ = "driver_locations"

    driver_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("drivers.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True, nullable=False
    )

    driver: Mapped["Driver"] = relationship("Driver", back_populates="locations")
