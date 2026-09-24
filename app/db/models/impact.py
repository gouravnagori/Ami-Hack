import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin, utc_now
from app.db.models.allocation import Allocation


class ImpactLedger(Base, UUIDPrimaryKeyMixin):
    """
    Append-only impact accounting ledger written exactly once upon delivery.
    """

    __tablename__ = "impact_ledger"

    allocation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("allocations.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    meals: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    co2e_kg: Mapped[float] = mapped_column(Float, nullable=False)
    delivered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    allocation: Mapped["Allocation"] = relationship("Allocation")
