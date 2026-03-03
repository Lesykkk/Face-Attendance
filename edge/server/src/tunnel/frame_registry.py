"""
FrameRegistry — in-memory registry of per-camera JPEG frame queues and
latest face detection + recognition results.

Shared between camera_pipeline (writer) and TunnelClient (reader).

Detection results are drawn by cv2 onto each BGR frame before JPEG encoding:
  - Green box  + similarity score  → recognized face
  - Yellow box + "?"               → detected but unrecognized / no active session
"""

import asyncio
import logging
import threading
from dataclasses import dataclass, field

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ── Visual style ────────────────────────────────────────────────────────────
_COLOR_MATCH   = (0, 230, 118)    # bright green (BGR) — recognized
_COLOR_UNKNOWN = (0, 0, 230)      # red (BGR)          — detected, no match
_BOX_THICKNESS = 2
_FONT          = cv2.FONT_HERSHEY_SIMPLEX
_FONT_SCALE    = 0.55
_FONT_THICK    = 1
_JPEG_QUALITY  = 70


@dataclass
class FaceDetectionResult:
    """Carries the bbox and optional recognition result for one detected face."""
    face_row: np.ndarray           # YuNet output row: [x, y, w, h, lm*5, score]
    match_score: float | None = None   # SFace cosine similarity (0..1), None = no match


class FrameRegistry:
    def __init__(self) -> None:
        self._queues: dict[int, asyncio.Queue[bytes]] = {}
        self._det_lock = threading.Lock()
        # camera_id → list of FaceDetectionResult
        self._detections: dict[int, list[FaceDetectionResult]] = {}

    # ── Registration ──────────────────────────────────────────────────────

    def register(self, camera_id: int) -> None:
        if camera_id not in self._queues:
            self._queues[camera_id] = asyncio.Queue(maxsize=2)
            logger.debug(f"[FrameRegistry] Registered camera {camera_id}")

    # ── Detection overlay ─────────────────────────────────────────────────

    def set_detections(self, camera_id: int, results: list[FaceDetectionResult]) -> None:
        """Store latest detection + recognition results for overlay drawing."""
        with self._det_lock:
            self._detections[camera_id] = results

    def _draw_overlays(self, frame: np.ndarray, camera_id: int) -> np.ndarray:
        with self._det_lock:
            results = list(self._detections.get(camera_id, []))

        if not results:
            return frame

        out = frame.copy()
        for det in results:
            x = int(det.face_row[0])
            y = int(det.face_row[1])
            w = int(det.face_row[2])
            h = int(det.face_row[3])

            if det.match_score is not None:
                color = _COLOR_MATCH
                label = f"{det.match_score:.2f}"
            else:
                color = _COLOR_UNKNOWN
                label = "?"

            # Bounding box
            cv2.rectangle(out, (x, y), (x + w, y + h), color, _BOX_THICKNESS)

            # Label above the box
            (tw, th), baseline = cv2.getTextSize(label, _FONT, _FONT_SCALE, _FONT_THICK)
            label_y = max(y - 6, th + baseline)
            cv2.putText(out, label, (x, label_y), _FONT, _FONT_SCALE, color, _FONT_THICK, cv2.LINE_AA)

        return out

    # ── Frame publishing ──────────────────────────────────────────────────

    def publish(self, camera_id: int, frame_bgr: np.ndarray) -> None:
        """Draw overlays, encode to JPEG, push to queue (drops oldest if full)."""
        queue = self._queues.get(camera_id)
        if queue is None:
            return

        rendered = self._draw_overlays(frame_bgr, camera_id)
        ok, buf = cv2.imencode(".jpg", rendered, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY])
        if not ok:
            return

        jpeg = buf.tobytes()
        if queue.full():
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        try:
            queue.put_nowait(jpeg)
        except asyncio.QueueFull:
            pass

    async def get_frame(self, camera_id: int) -> bytes | None:
        queue = self._queues.get(camera_id)
        if queue is None:
            return None
        return await queue.get()


# Module-level singleton
registry = FrameRegistry()
