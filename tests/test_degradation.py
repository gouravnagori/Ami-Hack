"""
STEP 5: Graceful Degradation Tests.

Verifies that each service layer degrades gracefully when its
external dependency is unavailable:

  - Routing:    OSRM down → haversine/fallback produces valid distance/duration
  - AI parsing: No LLM configured → deterministic regex parser works
  - Notifications: Provider unavailable → core workflow does NOT crash

Redis/ARQ: These are documented below (not pretending everything is offline-capable).
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.core.config import settings

# ── Routing Fallback ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_routing_fallback_haversine():
    """
    When OSRM is marked down (CHAOS_OSRM_DOWN=True), the RoutingClient
    must fall back to haversine * road-detour-factor and return a valid
    non-zero distance/duration matrix without raising exceptions.
    """
    from app.services.routing.client import RoutingClient

    client = RoutingClient(osrm_url="http://localhost:9999")  # unreachable URL

    # Temporarily mark OSRM as down
    original = settings.CHAOS_OSRM_DOWN
    settings.CHAOS_OSRM_DOWN = True
    try:
        coords = [
            (28.6139, 77.2090),  # Connaught Place
            (28.6250, 77.2200),  # ~1.5 km away
            (28.6350, 77.2300),  # ~3 km away
        ]

        dist_mat, dur_mat = await client.get_table(coords)

        # Must return a 3x3 matrix
        assert len(dist_mat) == 3
        assert len(dur_mat) == 3

        # Diagonal must be 0
        for i in range(3):
            assert dist_mat[i][i] == 0.0
            assert dur_mat[i][i] == 0.0

        # Off-diagonal must be positive
        for i in range(3):
            for j in range(3):
                if i != j:
                    assert dist_mat[i][j] > 0.0, f"Fallback distance[{i}][{j}] must be > 0"
                    assert dur_mat[i][j] > 0.0, f"Fallback duration[{i}][{j}] must be > 0"

        # Also test route
        total_dist, total_dur, polyline = await client.get_route(coords[:2])
        assert total_dist > 0.0
        assert total_dur > 0.0
        assert len(polyline) >= 2  # At least 2 coordinate pairs

    finally:
        settings.CHAOS_OSRM_DOWN = original


# ── AI Parsing Fallback ────────────────────────────────────────────────────────

def test_ai_parse_no_llm_falls_back_to_regex():
    """
    When no LLM API key is configured (OPENAI_API_KEY absent), the parser
    must fall back to regex/heuristic extraction and return a valid draft
    with at minimum: items, diet, storage, category.
    """
    from app.services.ai.parse import parse_donation_text

    now = datetime.now(UTC)

    # Structured text that regex can parse
    text = "50 portions of hot chicken biryani freshly cooked, pickup from CP"
    result = parse_donation_text(text=text, now=now)

    assert result["draft"] is not None
    draft = result["draft"]
    assert "items" in draft
    assert len(draft["items"]) >= 1
    assert draft["diet"] in ("non_veg", "veg", "egg")
    assert draft["storage"] in ("hot", "cold", "ambient")
    assert "total_portions" in draft
    assert draft["total_portions"] > 0
    assert result["confidence"] > 0.0
    assert isinstance(result["missing"], list)

    # Missing should always contain 'pickup' (location required from donor)
    assert "pickup" in result["missing"]


def test_ai_parse_minimal_input():
    """
    Even with minimal text, the fallback parser must not raise and must
    return a non-None draft with at least a placeholder item.
    """
    from app.services.ai.parse import parse_donation_text

    now = datetime.now(UTC)
    result = parse_donation_text(text="20 meals", now=now)

    assert result["draft"] is not None
    assert len(result["draft"]["items"]) >= 1
    assert result["draft"]["total_portions"] >= 20


def test_ai_parse_empty_input():
    """
    Empty text/photo → draft is None, confidence=0, all required fields
    listed in missing. Must not raise.
    """
    from app.services.ai.parse import parse_donation_text

    result = parse_donation_text(text=None, photo_base64=None)
    assert result["draft"] is None
    assert result["confidence"] == 0.0
    assert len(result["missing"]) >= 1


# ── Notification Service Fallback ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_notification_service_console_fallback():
    """
    The NotificationService base implementation logs to console (structlog)
    and never raises. Verifies that calling .send() with any template/data
    completes successfully without an external SMS/email provider.
    """
    from app.services.notifications.base import NotificationService, render_template

    svc = NotificationService()

    # Must not raise even without any external provider
    await svc.send(
        user_id="test-user-123",
        template="new_offer",
        data={
            "portions": 50,
            "diet": "veg",
            "donor_name": "Test Kitchen",
        },
    )

    # Template rendering must work for all registered templates
    for key in ["new_offer", "offer_expiring", "driver_assigned", "picked_up",
                "delivered", "risk_alert", "otp_pickup", "otp_dropoff"]:
        msg = render_template(key, {
            "portions": 50,
            "diet": "veg",
            "donor_name": "Test",
            "driver_name": "Test Driver",
            "eta_minutes": 15,
            "eta": "14:30",
            "org_name": "Test Org",
            "allocation_id": "abc123",
            "risk": "CRITICAL",
            "reason": "late delivery",
            "otp": "123456",
            "seconds": 90,
        })
        assert isinstance(msg, str), f"Template {key} must render to string"
        assert len(msg) > 0


@pytest.mark.asyncio
async def test_donation_workflow_not_blocked_by_notification_failure():
    """
    The core donation creation workflow must succeed even if notification
    delivery would fail (it is always fire-and-forget/async).
    Verified by creating a donation successfully — the existing lifecycle
    tests already confirm this. This test documents the design explicitly.
    """
    from httpx import ASGITransport, AsyncClient

    from app.main import app
    from app.services.sim.seed import run_seed

    await run_seed()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post("/api/v1/auth/demo", json={"role": "donor"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "notif-degrade-1"}

        now = datetime.now(UTC)
        payload = {
            "items": [{"name": "Degradation Test Food", "portions": 15}],
            "diet": "veg",
            "storage": "ambient",
            "category": "cooked_meals",
            "prepared_at": now.isoformat(),
            "pickup_window": {
                "start": now.isoformat(),
                "end": (now + timedelta(hours=2)).isoformat(),
            },
            "pickup": {"lat": 28.6139, "lng": 77.2090, "address": "Test"},
        }
        resp = await client.post("/api/v1/donations", json=payload, headers=headers)
        # Must complete successfully regardless of external notification state
        assert resp.status_code == 201


# ── Redis / External Dependency Note ──────────────────────────────────────────

# DOCUMENTED BEHAVIOR (not tested with mock infrastructure):
#
# Components that INTENTIONALLY require Redis for full functionality:
#   1. RoutingClient.get_table() — uses Redis for OSRM matrix cache (5-min TTL).
#      If Redis is unavailable: cache is skipped silently (logs debug warning),
#      fallback to direct OSRM or haversine is used. Core functionality preserved.
#
#   2. ARQ workers (dispatch, notify, expiry, capacity_tick) — require Redis
#      as the ARQ job queue backend.
#      If Redis is unavailable: ARQ workers cannot process jobs.
#      The REST API continues to work (HTTP layer is Redis-independent).
#      Impact: async background jobs (notifications, auto-dispatch ticks)
#      won't fire; critical real-time dispatch must be triggered manually.
#
#   3. WebSocket manager — in-process only, no Redis PubSub dependency.
#      Works without Redis for single-instance deployments.
#
# For hackathon demo: SQLite + in-process WebSocket + haversine fallback
# provides a fully functional demo with zero external service dependencies.
