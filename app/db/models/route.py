import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import StopStatus, StopType
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.allocation import Allocation
    from app.db.models.driver import Driver


class Route(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "routes"

    driver_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("drivers.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="planned", nullable=False
    )  # planned|active|completed|cancelled
    planned_distance_m: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    planned_duration_s: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    polyline: Mapped[list | None] = mapped_column(JSON, nullable=True)  # List of [lng, lat]
    replanned_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    saved_seconds_vs_previous: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    driver: Mapped["Driver"] = relationship("Driver", back_populates="routes")
    stops: Mapped[list["RouteStop"]] = relationship(
        "RouteStop", back_populates="route", cascade="all, delete-orphan", order_by="RouteStop.seq"
    )


class RouteStop(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "route_stops"

    route_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("routes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[StopType] = mapped_column(
        Enum(StopType, native_enum=False, length=20),
        nullable=False,
    )
    allocation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("allocations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Timings
    planned_arrival: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    predicted_arrival: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    slack_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Status & Handoff
    status: Mapped[StopStatus] = mapped_column(
        Enum(StopStatus, native_enum=False, length=20),
        default=StopStatus.PENDING,
        nullable=False,
    )
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    temp_c: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Recorded cold-chain drop temperature
    proof_photo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    route: Mapped["Route"] = relationship("Route", back_populates="stops")
    allocation: Mapped["Allocation"] = relationship("Allocation", back_populates="stops")

    __table_args__ = (Index("ix_route_stops_route_seq", "route_id", "seq"),)
