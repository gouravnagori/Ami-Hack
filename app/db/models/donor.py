import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.donation import Donation
    from app.db.models.user import User


class Donor(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "donors"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    org_name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(
        String(50), default="restaurant", nullable=False
    )  # restaurant|caterer|hostel_mess|event|grocer
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    lng: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    fssai_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    default_pickup_window: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # e.g. {"start": "21:00", "end": "23:00"}
    pickup_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    food_category: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    operating_hours: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="donor_profile")
    donations: Mapped[list["Donation"]] = relationship(
        "Donation", back_populates="donor", cascade="all, delete-orphan"
    )
