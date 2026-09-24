"""
WebSocket endpoint — api/v1/ws.py

Authenticates via JWT query param (?token=...).
Handles:
  - client → server: driver.location pings, ping
  - server → client: all GoldenHour events (Appendix A4)
  - replay: ?last_seq= triggers resend of the last 200 buffered events
    (approximated: sends a refetch directive instead if buffer is not available)
"""

import json
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from app.core.security import decode_token
from app.db.session import async_session_maker
from app.services.tracking import ingest_location
from app.ws import manager

router = APIRouter(tags=["realtime"])
logger = structlog.get_logger("goldenhour.ws")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = "", last_seq: int = 0):
    """
    Authenticate and serve real-time events.
    Query params:
      ?token=<JWT>         required
      ?last_seq=<int>      optional, for event replay on reconnect
    """
    # Auth: validate JWT from query param
    user_id: str | None = None
    role: str | None = None

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        role = payload.get("role")
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    await manager.connect(user_id, websocket)

    # If client reconnects with last_seq, instruct refetch (buffer not persisted in-memory)
    if last_seq > 0:
        await websocket.send_json({
            "event": "replay.refetch",
            "seq": 0,
            "ts": datetime.now(UTC).isoformat(),
            "data": {"reason": "In-memory buffer; please refetch state from REST endpoints."},
        })

    logger.info("ws.session_started", user_id=user_id, role=role)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            event = msg.get("event", "")

            if event == "ping":
                await websocket.send_json({
                    "event": "pong",
                    "seq": 0,
                    "ts": datetime.now(UTC).isoformat(),
                    "data": {},
                })

            elif event == "driver.location" and role == "driver":
                data = msg.get("data", {})
                lat = data.get("lat")
                lng = data.get("lng")
                speed = data.get("speed", 0.0)
                heading = data.get("heading", 0.0)
                if lat is not None and lng is not None:
                    async with async_session_maker() as db:
                        from app.db.models.driver import Driver
                        driver_stmt = select(Driver).where(Driver.user_id == user_id)
                        driver = (await db.execute(driver_stmt)).scalar_one_or_none()
                        if driver:
                            result = await ingest_location(
                                db,
                                driver_id=driver.id,
                                lat=float(lat),
                                lng=float(lng),
                                speed=float(speed),
                                heading=float(heading),
                            )
                            # Emit risk alerts to admin/ops
                            for alert in result.get("risk_alerts", []):
                                await manager.broadcast_all("alert.risk", alert)

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(user_id, websocket)
        logger.info("ws.session_ended", user_id=user_id)
