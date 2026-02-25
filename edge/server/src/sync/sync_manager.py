"""
SyncManager — periodically fetches session/embedding data from Central Server
and maintains in-memory state that camera pipeline tasks read from.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime

import httpx
import numpy as np

from pipeline.matcher import PersonEmbeddings

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    session_id: int
    start_time: datetime
    end_time: datetime
    students: list[PersonEmbeddings]


@dataclass
class SyncState:
    # camera rtsp_url → list of active sessions
    camera_sessions: dict[str, list[SessionState]] = field(default_factory=dict)


class SyncManager:
    def __init__(self, base_url: str, api_key: str, interval_seconds: int) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        self._interval = interval_seconds
        self._lock = asyncio.Lock()
        self._state = SyncState()
        self._synced_event = asyncio.Event()  # set after first successful sync

    async def get_state(self) -> SyncState:
        async with self._lock:
            return self._state

    async def wait_for_first_sync(self) -> None:
        await self._synced_event.wait()

    async def _do_sync(self) -> None:
        try:
            response = await self._client.get("/api/edge/sync")
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"[Sync] Server error {e.response.status_code}: {e.response.text}")
            return
        except httpx.RequestError as e:
            logger.error(f"[Sync] Network error: {e}")
            return

        new_camera_sessions: dict[str, list[SessionState]] = {}

        for session_data in data.get("sessions", []):
            rtsp = session_data["camera_rtsp"]

            def _normalize(v: list[float]) -> np.ndarray:
                vec = np.array(v, dtype=np.float32)
                norm = np.linalg.norm(vec)
                return vec / norm if norm > 0 else vec

            students = [
                PersonEmbeddings(
                    person_id=int(s["person_id"]),
                    embeddings=[_normalize(e) for e in s["embeddings"]],
                )
                for s in session_data.get("students", [])
            ]
            state = SessionState(
                session_id=int(session_data["session_id"]),
                start_time=datetime.fromisoformat(session_data["start_time"]),
                end_time=datetime.fromisoformat(session_data["end_time"]),
                students=students,
            )
            new_camera_sessions.setdefault(rtsp, []).append(state)

        async with self._lock:
            self._state = SyncState(camera_sessions=new_camera_sessions)

        camera_count = len(new_camera_sessions)
        session_count = sum(len(v) for v in new_camera_sessions.values())
        logger.info(f"[Sync] Updated: {camera_count} camera(s), {session_count} active session(s)")
        self._synced_event.set()

    async def run(self) -> None:
        """Background task: sync immediately, then every interval."""
        logger.info("[Sync] Starting sync manager...")
        while True:
            await self._do_sync()
            await asyncio.sleep(self._interval)

    async def aclose(self) -> None:
        await self._client.aclose()
