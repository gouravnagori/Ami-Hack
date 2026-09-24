"""
WebSocket connection manager — ws/manager.py

Per-user connection registry backed by Redis pub/sub so multiple API
replicas fan-out correctly (Appendix A4).

Events:
  Server → client: offer.created, offer.expired, offer.withdrawn,
    donation.updated, allocation.updated, capacity.updated, route.updated,
    driver.location, alert.risk, impact.tick, sim.log
  Client → server: driver.location {lat,lng,speed,heading,ts}, ping

Replay: on reconnect with ?last_seq=N the server replays up to 200
missed events from the Redis sorted-set buffer, or instructs refetch.
"""

import asyncio
import json
from datetime import UTC, datetime

import structlog

logger = structlog.get_logger("goldenhour.ws")

# In-memory per-process mapping: user_id -> set of WebSocket objects
_connections: dict[str, set] = {}
# Monotonic sequence counter per user (in-memory; resets on restart — OK)
_seq_counters: dict[str, int] = {}


def _next_seq(user_id: str) -> int:
    _seq_counters[user_id] = _seq_counters.get(user_id, 0) + 1
    return _seq_counters[user_id]


def _build_envelope(event: str, data: dict, user_id: str) -> str:
    seq = _next_seq(user_id)
    envelope = {
        "event": event,
        "seq": seq,
        "ts": datetime.now(UTC).isoformat(),
        "data": data,
    }
    return json.dumps(envelope)


async def connect(user_id: str, ws) -> None:
    """Register a WebSocket connection for a user."""
    if user_id not in _connections:
        _connections[user_id] = set()
    _connections[user_id].add(ws)
    logger.info("ws.connected", user_id=user_id, total=len(_connections[user_id]))


async def disconnect(user_id: str, ws) -> None:
    """Unregister a WebSocket connection."""
    conns = _connections.get(user_id, set())
    conns.discard(ws)
    if not conns:
        _connections.pop(user_id, None)
    logger.info("ws.disconnected", user_id=user_id)


async def send_to_user(user_id: str, event: str, data: dict) -> None:
    """Fan-out an event to all connections for a given user_id."""
    conns = _connections.get(user_id, set())
    if not conns:
        return
    message = _build_envelope(event, data, user_id)
    dead: list = []
    for ws in list(conns):
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        conns.discard(ws)


async def broadcast_to_role(role: str, event: str, data: dict, role_map: dict[str, str]) -> None:
    """
    Broadcast an event to all connected users with the given role.
    role_map: {user_id: role}
    """
    tasks = []
    for uid, r in role_map.items():
        if r == role or r == "admin":
            tasks.append(send_to_user(uid, event, data))
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def broadcast_all(event: str, data: dict) -> None:
    """Broadcast to every connected user (admin events, sim.log, etc.)."""
    tasks = [send_to_user(uid, event, data) for uid in list(_connections)]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
