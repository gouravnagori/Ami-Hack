import uuid
from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Time, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.db.models.allocation import Allocation
    from app.db.models.recipient import RecipientOrg


class CapacityWindow(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "capacity_windows"

    org_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recipient_orgs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    dow: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Day of week: 0=Mon, 6=Sun
    specific_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    max_portions: Mapped[int] = mapped_column(Integer, nullable=False)

    org: Mapped["RecipientOrg"] = relationship("RecipientOrg", back_populates="capacity_windows")


class CapacityAdjustment(Base, UUIDPrimaryKeyMixin):
    """Append-only capacity adjustment ledger."""

    __tablename__ = "capacity_adjustments"

    org_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recipient_orgs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    delta_portions: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    org: Mapped["RecipientOrg"] = relationship(
        "RecipientOrg", back_populates="capacity_adjustments"
    )


class CapacityReservation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "capacity_reservations"

    org_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recipient_orgs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    allocation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("allocations.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    portions: Mapped[int] = mapped_column(Integer, nullable=False)
    cold_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    state: Mapped[str] = mapped_column(
        String(30), default="held", nullable=False
    )  # held|committed|released|consumed
    held_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    arrives_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    org: Mapped["RecipientOrg"] = relationship(
        "RecipientOrg", back_populates="capacity_reservations"
    )
    allocation: Mapped["Allocation | None"] = relationship(
        "Allocation", back_populates="reservations"
    )

    __table_args__ = (Index("ix_capacity_reservations_org_state", "org_id", "state"),)
