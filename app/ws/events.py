"""
WebSocket event helpers — ws/events.py

Typed helpers for emitting the standard GoldenHour events (Appendix A4).
"""

from app.ws import manager


async def emit_offer_created(user_id: str, offer: dict) -> None:
    await manager.send_to_user(user_id, "offer.created", offer)


async def emit_offer_expired(user_id: str, offer_id: str) -> None:
    await manager.send_to_user(user_id, "offer.expired", {"offer_id": offer_id})


async def emit_offer_withdrawn(user_id: str, offer_id: str) -> None:
    await manager.send_to_user(user_id, "offer.withdrawn", {"offer_id": offer_id})


async def emit_donation_updated(user_id: str, donation: dict) -> None:
    await manager.send_to_user(user_id, "donation.updated", donation)


async def emit_allocation_updated(user_id: str, allocation: dict) -> None:
    await manager.send_to_user(user_id, "allocation.updated", allocation)


async def emit_capacity_updated(user_id: str, snapshot: dict) -> None:
    await manager.send_to_user(user_id, "capacity.updated", snapshot)


async def emit_route_updated(user_id: str, route: dict) -> None:
    await manager.send_to_user(user_id, "route.updated", route)


async def emit_driver_location(user_id: str, location: dict) -> None:
    """Backpressure: drop driver.location events for slow consumers (fire-and-forget)."""
    await manager.send_to_user(user_id, "driver.location", location)


async def emit_alert_risk(user_id: str, alert: dict) -> None:
    await manager.send_to_user(user_id, "alert.risk", alert)


async def emit_impact_tick(summary: dict) -> None:
    await manager.broadcast_all("impact.tick", summary)


async def emit_sim_log(message: str) -> None:
    await manager.broadcast_all("sim.log", {"message": message})
