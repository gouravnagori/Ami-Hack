from sqlalchemy import Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import StorageCondition
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FoodSafetyRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Food safety parameters per storage condition and food category.
    NOTE: Placeholder values seeded — VALIDATE WITH FSSAI / LOCAL FOOD-SAFETY GUIDANCE BEFORE PILOT.
    """

    __tablename__ = "food_safety_rules"

    storage: Mapped[StorageCondition] = mapped_column(
        Enum(StorageCondition, native_enum=False, length=20),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    max_hours: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # Max allowed time from preparation to consumption
    transit_cap_minutes: Mapped[int] = mapped_column(
        Integer, default=60, nullable=False
    )  # Max time allowed in vehicle
    handling_buffer_minutes: Mapped[int] = mapped_column(
        Integer, default=15, nullable=False
    )  # Service buffer before safe_until
