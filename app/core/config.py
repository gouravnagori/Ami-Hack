import json
from enum import StrEnum
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class Role(StrEnum):
    DONOR = "donor"
    RECIPIENT = "recipient"
    DRIVER = "driver"
    ADMIN = "admin"


class DietType(StrEnum):
    VEG = "veg"
    EGG = "egg"
    NON_VEG = "non_veg"


class StorageCondition(StrEnum):
    AMBIENT = "ambient"
    HOT = "hot"
    COLD = "cold"


class DonationStatus(StrEnum):
    DRAFT = "draft"
    POSTED = "posted"
    MATCHING = "matching"
    PARTIALLY_MATCHED = "partially_matched"
    MATCHED = "matched"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    EXPIRED = "expired"
    FALLBACK = "fallback"
    CANCELLED = "cancelled"


class AllocationStatus(StrEnum):
    OFFERED = "offered"
    ACCEPTED = "accepted"
    DRIVER_PENDING = "driver_pending"
    DRIVER_ASSIGNED = "driver_assigned"
    PICKED_UP = "picked_up"
    DELIVERED = "delivered"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OfferKind(StrEnum):
    RECIPIENT = "recipient"
    DRIVER = "driver"


class OfferStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class StopType(StrEnum):
    PICKUP = "pickup"
    DROPOFF = "dropoff"


class StopStatus(StrEnum):
    PENDING = "pending"
    ARRIVED = "arrived"
    DONE = "done"
    SKIPPED = "skipped"
    FAILED = "failed"


class DriverStatus(StrEnum):
    OFFLINE = "offline"
    AVAILABLE = "available"
    ON_TASK = "on_task"
    STALE = "stale"


class VehicleType(StrEnum):
    BICYCLE = "bicycle"
    SCOOTER = "scooter"
    E_RICKSHAW = "e_rickshaw"
    VAN = "van"


class Risk(StrEnum):
    SAFE = "safe"
    TIGHT = "tight"
    CRITICAL = "critical"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=False,
    )

    # Application
    APP_ENV: AppEnv = AppEnv.DEVELOPMENT
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    PROJECT_NAME: str = "GoldenHour API"
    API_V1_PREFIX: str = "/api/v1"

    # Security & Auth
    SECRET_KEY: str = "goldenhour-insecure-dev-secret-key-change-in-production-min32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DEMO_MODE: bool = True
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            if v.startswith("["):
                return json.loads(v)
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Database & Redis
    DATABASE_URL: str = "sqlite+aiosqlite:///./goldenhour.db"
    DATABASE_ECHO: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"

    # Spatial & Seed
    SEED_CENTER_LAT: float = 28.6139
    SEED_CENTER_LNG: float = 77.2090
    SEED_RADIUS_KM: float = 15.0

    # Routing
    OSRM_URL: str = "http://localhost:5000"
    MATRIX_CACHE_TTL_SECONDS: int = 300

    # Operational Parameters
    DISPATCH_TICK_SECONDS: int = 10
    RISK_MONITOR_SECONDS: int = 15
    STALE_DRIVER_SECONDS: int = 90
    STALE_DRIVER_REASSIGN_SECONDS: int = 180
    CO2E_PER_KG: float = 2.5
    PORTION_KG: float = 0.4

    # AI Feature Flags
    AGENT_ENABLED: bool = False
    LLM_PARSE_MODEL: str = "gemini-1.5-flash"
    LLM_AGENT_MODEL: str = "gemini-1.5-pro"
    LLM_API_KEY: str = ""

    # Chaos Injection Flags
    CHAOS_OSRM_DOWN: bool = False
    CHAOS_DRIVER_DROP: bool = False
    CHAOS_ORG_FULL: bool = False
    CHAOS_TRAFFIC_SPIKE: bool = False


settings = Settings()
