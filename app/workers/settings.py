"""
ARQ worker settings — workers/settings.py

Configures the ARQ worker with all registered background job functions.
Run with: arq workers.settings.WorkerSettings
"""

from arq.connections import RedisSettings as ArqRedisSettings

from app.core.config import settings

# Re-export for ARQ's worker discovery
from app.workers.jobs import (
    capacity_tick,
    dispatch_tick,
    notify,
    offer_expiry,
    risk_monitor,
    stale_driver_check,
)


class WorkerSettings:
    """ARQ worker configuration (Section 8)."""

    functions = [
        dispatch_tick,
        offer_expiry,
        risk_monitor,
        stale_driver_check,
        capacity_tick,
        notify,
    ]

    redis_settings = ArqRedisSettings.from_dsn(settings.REDIS_URL)

    # Default job timeout: 30 s
    job_timeout = 30

    # Health heartbeat key written to Redis so /readyz can check worker liveness
    health_check_key = "goldenhour:worker:heartbeat"
    health_check_interval = 30

    # cron-style scheduled jobs via ARQ cron
    cron_jobs = []  # Jobs are enqueued directly by the dispatch loop
