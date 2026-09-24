from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.core.clock import Clock
from app.core.deps import get_clock
from app.db.session import check_db_health, check_redis_health

router = APIRouter(tags=["Health"])


@router.get("/healthz", summary="Process liveness probe")
async def healthz():
    """Returns 200 OK if the API process is alive and responsive."""
    return {"status": "ok", "service": "goldenhour-api"}


@router.get("/readyz", summary="Service readiness probe")
async def readyz():
    """Checks connectivity to PostgreSQL database and Redis."""
    db_ok = await check_db_health()
    redis_ok = await check_redis_health()

    is_ready = db_ok  # If redis is degraded, we still allow degraded readiness
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if is_ready else "degraded",
            "dependencies": {
                "database": "connected" if db_ok else "unreachable",
                "redis": "connected" if redis_ok else "unreachable",
            },
        },
    )


@router.get("/time", summary="Server UTC time for client clock skew correction")
async def get_server_time(clock: Clock = Depends(get_clock)):
    now = clock.now()
    return {
        "server_time": now.isoformat(),
        "timestamp": int(now.timestamp()),
        "timezone": "UTC",
    }
