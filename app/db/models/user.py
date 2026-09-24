from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import Role
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    role: Mapped[Role] = mapped_column(
        Enum(Role, native_enum=False, length=20),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    locale: Mapped[str] = mapped_column(String(10), default="en", nullable=False)

    # Relationships
    donor_profile: Mapped["Donor | None"] = relationship(
        "Donor", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    recipient_profile: Mapped["RecipientOrg | None"] = relationship(
        "RecipientOrg", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    driver_profile: Mapped["Driver | None"] = relationship(
        "Driver", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


from app.db.models.donor import Donor  # noqa: E402
from app.db.models.driver import Driver  # noqa: E402
from app.db.models.recipient import RecipientOrg  # noqa: E402
