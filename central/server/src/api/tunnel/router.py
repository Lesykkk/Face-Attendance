import base64
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from core.database import get_db
from core.security import hash_api_key
from core.tunnel_registry import registry as tunnel_registry
from models.edge_node import EdgeNode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tunnel", tags=["Tunnel"])


async def _authenticate_edge_node(ws: WebSocket) -> EdgeNode | None:
    """Read Authorization header, verify via HMAC-SHA256, return EdgeNode or None."""
    auth = ws.headers.get("authorization", "")
    api_key = auth.removeprefix("Bearer ").strip()
    if not api_key:
        return None

    key_hash = hash_api_key(api_key)
    async for db in get_db():
        result = await db.execute(
            select(EdgeNode).where(EdgeNode.api_key_hash == key_hash)
        )
        return result.scalar_one_or_none()
    return None


@router.websocket("/ws")
async def tunnel_ws(ws: WebSocket):
    """WebSocket endpoint for Edge Node reverse tunnel."""
    await ws.accept()

    node = await _authenticate_edge_node(ws)
    if node is None:
        await ws.close(code=4001, reason="Unauthorized")
        logger.warning("[Tunnel WS] Rejected unauthenticated connection.")
        return

    tunnel_registry.register_node(node.id, ws)

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"[Tunnel WS] Non-JSON from node {node.id}: {raw!r}")
                continue

            msg_type = msg.get("type")

            if msg_type == "frame":
                stream_id: str = msg.get("stream_id", "")
                data_b64: str = msg.get("data", "")
                if stream_id and data_b64:
                    try:
                        jpeg = base64.b64decode(data_b64)
                        tunnel_registry.push_frame(stream_id, jpeg)
                    except Exception as exc:
                        logger.debug(f"[Tunnel WS] Frame decode error: {exc}")
            else:
                logger.debug(f"[Tunnel WS] Unknown message type from node {node.id}: {msg_type!r}")

    except WebSocketDisconnect:
        logger.info(f"[Tunnel WS] Edge Node {node.id} disconnected.")
    except Exception as exc:
        logger.warning(f"[Tunnel WS] Unexpected error for node {node.id}: {exc}")
    finally:
        tunnel_registry.unregister_node(node.id)
