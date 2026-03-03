"""
WebSocket endpoint: /ws

Broadcasts device-related events to all connected clients.
Message format:
  {
    "event": "device_updated" | "device_deleted" | "device_status_changed",
    "data": {...}
  }
"""
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ws"])

_subscribers: list[WebSocket] = []


async def broadcast(event: str, data: dict):
    message = json.dumps({"event": event, "data": data})
    dead = []
    for ws in _subscribers:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _subscribers.remove(ws)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _subscribers.append(websocket)
    logger.info("WebSocket client connected (total: %d)", len(_subscribers))
    try:
        while True:
            # Keep connection alive; client may send ping frames
            await websocket.receive_text()
    except WebSocketDisconnect:
        _subscribers.remove(websocket)
        logger.info("WebSocket client disconnected (total: %d)", len(_subscribers))
