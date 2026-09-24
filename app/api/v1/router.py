from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.allocations import router as allocations_router
from app.api.v1.auth import router as auth_router
from app.api.v1.donations import router as donations_router
from app.api.v1.driver import router as driver_router
from app.api.v1.health import router as health_router
from app.api.v1.impact import router as impact_router
from app.api.v1.offers import router as offers_router
from app.api.v1.org import router as org_router
from app.api.v1.stops import router as stops_router
from app.api.v1.ws import router as ws_router

api_v1_router = APIRouter()

# Mount API routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(donations_router)
api_v1_router.include_router(org_router)
api_v1_router.include_router(offers_router)
api_v1_router.include_router(driver_router)
api_v1_router.include_router(stops_router)
api_v1_router.include_router(allocations_router)
api_v1_router.include_router(impact_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(ws_router)

