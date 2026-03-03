"""
TunnelRegistry — in-memory store for active Edge Node WebSocket connections
and per-stream JPEG frame queues.

This is a module-level singleton shared across all FastAPI request handlers.

Two separate dictionaries:
  - _tunnels:  node_id (int) → WebSocket connection from that Edge Node
  - _streams:  stream_id (str) → asyncio.Queue[bytes | None]
               (None sentinel signals end-of-stream to the consumer)
"""

import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class TunnelRegistry:
    def __init__(self) -> None:
        # node_id → active WebSocket
        self._tunnels: dict[int, WebSocket] = {}
        # stream_id → Queue of raw JPEG bytes (None = stream ended)
        self._streams: dict[str, asyncio.Queue[bytes | None]] = {}

    # ── Tunnel management ──────────────────────────────────────────────────

    def register_node(self, node_id: int, ws: WebSocket) -> None:
        self._tunnels[node_id] = ws
        logger.info(f"[TunnelRegistry] Edge Node {node_id} connected.")

    def unregister_node(self, node_id: int) -> None:
        self._tunnels.pop(node_id, None)
        logger.info(f"[TunnelRegistry] Edge Node {node_id} disconnected.")

    def is_online(self, node_id: int) -> bool:
        return node_id in self._tunnels

    async def send_command(self, node_id: int, payload: dict) -> bool:
        """Send a JSON command to an Edge Node. Returns False if not connected."""
        ws = self._tunnels.get(node_id)
        if ws is None:
            return False
        try:
            await ws.send_json(payload)
            return True
        except Exception as exc:
            logger.warning(f"[TunnelRegistry] Failed to send command to node {node_id}: {exc}")
            return False

    # ── Stream management ─────────────────────────────────────────────────

    def create_stream(self, stream_id: str) -> asyncio.Queue[bytes | None]:
        """Create a frame queue for a new stream. Returns the queue."""
        q: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=30)
        self._streams[stream_id] = q
        logger.debug(f"[TunnelRegistry] Stream created: {stream_id}")
        return q

    def get_stream(self, stream_id: str) -> asyncio.Queue[bytes | None] | None:
        return self._streams.get(stream_id)

    def push_frame(self, stream_id: str, jpeg: bytes) -> None:
        """Non-blocking push. Drops oldest frame if queue is full."""
        q = self._streams.get(stream_id)
        if q is None:
            return
        if q.full():
            try:
                q.get_nowait()
            except asyncio.QueueEmpty:
                pass
        try:
            q.put_nowait(jpeg)
        except asyncio.QueueFull:
            pass

    def close_stream(self, stream_id: str) -> None:
        """Signal end-of-stream and remove the queue."""
        q = self._streams.pop(stream_id, None)
        if q:
            try:
                q.put_nowait(None)  # sentinel
            except asyncio.QueueFull:
                pass
        logger.debug(f"[TunnelRegistry] Stream closed: {stream_id}")


# Module-level singleton
registry = TunnelRegistry()
