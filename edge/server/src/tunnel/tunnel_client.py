"""
TunnelClient — maintains a persistent WebSocket connection to Central Server.

Responsibilities:
  - Authenticate with EDGE_API_KEY on connect.
  - Auto-reconnect with exponential backoff on any failure.
  - Handle incoming commands from Central Server:
      {"type": "start_stream", "camera_id": <int>, "stream_id": "<uuid>"}
      {"type": "stop_stream",  "stream_id": "<uuid>"}
  - For each active stream: read JPEG frames from FrameRegistry and
    send them back through the WebSocket as binary messages framed as:
      {"type": "frame", "stream_id": "<uuid>", "data": "<base64-jpeg>"}
  - Keepalive: respond to ping with pong (websockets library handles
    protocol-level ping/pong automatically).
"""

import asyncio
import base64
import json
import logging

import websockets
from websockets.exceptions import ConnectionClosed

from tunnel.frame_registry import registry

logger = logging.getLogger(__name__)

_BACKOFF_INITIAL = 2.0
_BACKOFF_MAX = 60.0
# Target FPS for preview streams (no need for full camera FPS)
_PREVIEW_FPS = 10
_FRAME_INTERVAL = 1.0 / _PREVIEW_FPS


class TunnelClient:
    """
    Manages a persistent WebSocket tunnel to Central Server.
    Spawns per-stream asyncio tasks that push JPEG frames received
    from FrameRegistry through the WebSocket.
    """

    def __init__(self, central_server_url: str, api_key: str) -> None:
        # Convert http(s) base URL to ws(s) tunnel endpoint
        ws_base = central_server_url.replace("https://", "wss://").replace("http://", "ws://")
        self._ws_url = f"{ws_base.rstrip('/')}/api/tunnel/ws"
        self._api_key = api_key
        # stream_id → asyncio.Task
        self._stream_tasks: dict[str, asyncio.Task] = {}

    async def run(self) -> None:
        """Entry point — runs forever, reconnecting on any error."""
        backoff = _BACKOFF_INITIAL
        while True:
            try:
                await self._connect_and_serve()
                backoff = _BACKOFF_INITIAL  # reset after clean disconnect
            except asyncio.CancelledError:
                logger.info("[Tunnel] Cancelled — shutting down.")
                await self._cancel_all_streams()
                return
            except Exception as exc:
                logger.warning(f"[Tunnel] Disconnected ({exc}). Reconnecting in {backoff:.0f}s...")
                await self._cancel_all_streams()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _BACKOFF_MAX)

    async def _connect_and_serve(self) -> None:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        logger.info(f"[Tunnel] Connecting to {self._ws_url} ...")

        async with websockets.connect(self._ws_url, additional_headers=headers) as ws:
            logger.info("[Tunnel] Connected to Central Server.")
            async for raw in ws:
                await self._handle_message(raw, ws)

    async def _handle_message(self, raw: str | bytes, ws) -> None:
        try:
            msg = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"[Tunnel] Received non-JSON message: {raw!r}")
            return

        msg_type = msg.get("type")

        if msg_type == "start_stream":
            camera_id: int = msg["camera_id"]
            stream_id: str = msg["stream_id"]
            registry.register(camera_id)
            logger.info(f"[Tunnel] start_stream: camera_id={camera_id} stream_id={stream_id}")
            task = asyncio.create_task(
                self._stream_frames(camera_id, stream_id, ws),
                name=f"stream_{stream_id}",
            )
            self._stream_tasks[stream_id] = task

        elif msg_type == "stop_stream":
            stream_id: str = msg["stream_id"]
            logger.info(f"[Tunnel] stop_stream: stream_id={stream_id}")
            await self._cancel_stream(stream_id)

        else:
            logger.debug(f"[Tunnel] Unknown message type: {msg_type!r}")

    async def _stream_frames(self, camera_id: int, stream_id: str, ws) -> None:
        """Reads JPEG frames from FrameRegistry and sends them through the WS."""
        logger.info(f"[Tunnel] Stream started: stream_id={stream_id} camera_id={camera_id}")
        try:
            while True:
                frame_start = asyncio.get_event_loop().time()

                jpeg = await registry.get_frame(camera_id)
                if jpeg is None:
                    # Camera not registered — wait and retry
                    await asyncio.sleep(0.5)
                    continue

                payload = json.dumps({
                    "type": "frame",
                    "stream_id": stream_id,
                    "data": base64.b64encode(jpeg).decode(),
                })
                try:
                    await ws.send(payload)
                except ConnectionClosed:
                    logger.info(f"[Tunnel] WS closed while streaming stream_id={stream_id}")
                    return

                # Throttle to _PREVIEW_FPS
                elapsed = asyncio.get_event_loop().time() - frame_start
                sleep_for = max(0.0, _FRAME_INTERVAL - elapsed)
                if sleep_for > 0:
                    await asyncio.sleep(sleep_for)

        except asyncio.CancelledError:
            logger.info(f"[Tunnel] Stream task cancelled: stream_id={stream_id}")
        finally:
            self._stream_tasks.pop(stream_id, None)

    async def _cancel_stream(self, stream_id: str) -> None:
        task = self._stream_tasks.pop(stream_id, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def _cancel_all_streams(self) -> None:
        for stream_id in list(self._stream_tasks):
            await self._cancel_stream(stream_id)
