"""
AttendanceReporter — sends attendance events to the Central Server.
Uses a persistent httpx.AsyncClient for connection reuse.
"""

import logging
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class AttendanceReporter:
    def __init__(self, base_url: str, api_key: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )

    async def report(
        self,
        person_id: int,
        session_id: int,
        timestamp: datetime,
        confidence: float,
    ) -> None:
        payload = {
            "person_id": person_id,
            "session_id": session_id,
            "timestamp": timestamp.isoformat(),
            "confidence": confidence,
        }
        try:
            response = await self._client.post("/api/edge/attendance", json=payload)
            response.raise_for_status()
            logger.debug(f"[Reporter] Reported person {person_id} for session {session_id}")
        except httpx.HTTPStatusError as e:
            logger.error(f"[Reporter] Server returned {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"[Reporter] Network error: {e}")

    async def aclose(self) -> None:
        await self._client.aclose()
