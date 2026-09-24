"""
OSRM Routing Client with Redis Matrix Cache and Graceful Fallback.

Capabilities:
- Primary: OSRM /table and /route endpoints
- Cache: Redis matrix cache keyed by coordinates (rounded to 5 decimals) + 5-minute bucket
- Fallback: Haversine distance * 1.35 detour factor + vehicle speed profile + traffic factor
- Chaos testing support via settings.CHAOS_OSRM_DOWN
"""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import VehicleType, settings
from app.core.logging import get_logger
from app.services.matching import haversine_distance_m
from app.services.routing.eta import (
    ROAD_DETOUR_FACTOR,
    estimate_travel_duration_s,
)

logger = get_logger(__name__)


class RoutingClient:
    def __init__(self, osrm_url: str | None = None, redis_client: Any | None = None):
        self.osrm_url = osrm_url or settings.OSRM_URL
        self.redis = redis_client
        self._http_client: httpx.AsyncClient | None = None

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=2.0)
        return self._http_client

    async def close(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def _cache_key(self, coords: list[tuple[float, float]], now: datetime) -> str:
        rounded = [f"{lat:.5f},{lng:.5f}" for lat, lng in coords]
        bucket = int(now.timestamp() // 300)
        h = hashlib.sha256(";".join(rounded).encode()).hexdigest()[:16]
        return f"osrm:table:{h}:{bucket}"

    async def get_table(
        self,
        coordinates: list[tuple[float, float]],
        vehicle: VehicleType = VehicleType.SCOOTER,
        dt: datetime | None = None,
    ) -> tuple[list[list[float]], list[list[float]]]:
        """
        Compute NxN distance (meters) and duration (seconds) matrices.
        coordinates: list of (lat, lng) pairs.
        Returns: (distance_matrix_m, duration_matrix_s)
        """
        n = len(coordinates)
        if n == 0:
            return [], []
        if n == 1:
            return [[0.0]], [[0.0]]

        if dt is None:
            dt = datetime.now(UTC)

        # Check chaos flag
        if getattr(settings, "CHAOS_OSRM_DOWN", False):
            return self._fallback_table(coordinates, vehicle, dt)

        # Try cache
        cache_key = self._cache_key(coordinates, dt)
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    return data["distances"], data["durations"]
            except Exception as e:
                logger.debug("redis_cache_miss_or_error", error=str(e))

        # Try OSRM table
        try:
            # OSRM expects {lng},{lat}
            coords_str = ";".join(f"{lng:.6f},{lat:.6f}" for lat, lng in coordinates)
            url = f"{self.osrm_url}/table/v1/driving/{coords_str}?annotations=duration,distance"
            client = await self._get_http()
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "Ok":
                    distances = data.get("distances", [])
                    durations = data.get("durations", [])
                    # Cache successful result
                    if self.redis:
                        try:
                            await self.redis.setex(
                                cache_key,
                                settings.MATRIX_CACHE_TTL_SECONDS,
                                json.dumps({"distances": distances, "durations": durations}),
                            )
                        except Exception:
                            pass
                    return distances, durations
        except Exception as e:
            logger.warning("osrm_table_failed_falling_back", error=str(e))

        # Fallback to haversine * 1.35
        return self._fallback_table(coordinates, vehicle, dt)

    async def get_route(
        self,
        coordinates: list[tuple[float, float]],
        vehicle: VehicleType = VehicleType.SCOOTER,
        dt: datetime | None = None,
    ) -> tuple[float, float, list[list[float]]]:
        """
        Compute route along ordered waypoints.
        coordinates: list of (lat, lng)
        Returns: (total_distance_m, total_duration_s, polyline_geojson_coords)
        where polyline_geojson_coords is list of [lng, lat]
        """
        if len(coordinates) < 2:
            return 0.0, 0.0, [[lng, lat] for lat, lng in coordinates]

        if dt is None:
            dt = datetime.now(UTC)

        if not getattr(settings, "CHAOS_OSRM_DOWN", False):
            try:
                coords_str = ";".join(f"{lng:.6f},{lat:.6f}" for lat, lng in coordinates)
                url = f"{self.osrm_url}/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
                client = await self._get_http()
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == "Ok" and data.get("routes"):
                        best = data["routes"][0]
                        dist = float(best.get("distance", 0.0))
                        dur = float(best.get("duration", 0.0))
                        poly = best.get("geometry", {}).get("coordinates", [])
                        return dist, dur, poly
            except Exception as e:
                logger.warning("osrm_route_failed_falling_back", error=str(e))

        return self._fallback_route(coordinates, vehicle, dt)

    def _fallback_table(
        self,
        coords: list[tuple[float, float]],
        vehicle: VehicleType,
        dt: datetime,
    ) -> tuple[list[list[float]], list[list[float]]]:
        n = len(coords)
        dist_mat: list[list[float]] = [[0.0] * n for _ in range(n)]
        dur_mat: list[list[float]] = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                lat1, lng1 = coords[i]
                lat2, lng2 = coords[j]
                straight_dist = haversine_distance_m(lat1, lng1, lat2, lng2)
                road_dist = straight_dist * ROAD_DETOUR_FACTOR
                dist_mat[i][j] = road_dist
                dur_mat[i][j] = estimate_travel_duration_s(road_dist, vehicle, dt)

        return dist_mat, dur_mat

    def _fallback_route(
        self,
        coords: list[tuple[float, float]],
        vehicle: VehicleType,
        dt: datetime,
    ) -> tuple[float, float, list[list[float]]]:
        total_dist = 0.0
        total_dur = 0.0
        polyline: list[list[float]] = []

        for i in range(len(coords)):
            lat, lng = coords[i]
            polyline.append([lng, lat])
            if i > 0:
                p_lat, p_lng = coords[i - 1]
                dist = haversine_distance_m(p_lat, p_lng, lat, lng) * ROAD_DETOUR_FACTOR
                total_dist += dist
                total_dur += estimate_travel_duration_s(dist, vehicle, dt)

        return total_dist, total_dur, polyline


# Global singleton routing client
routing_client = RoutingClient()
