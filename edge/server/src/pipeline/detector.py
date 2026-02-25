"""
YuNet face detector wrapper — offloads cv2.FaceDetectorYN.detect() to a
ThreadPoolExecutor so it never blocks the asyncio event loop.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class FaceDetector:
    def __init__(self, model_path: str, executor: ThreadPoolExecutor) -> None:
        self._executor = executor
        # Each instance has its own cv2 detector (not thread-safe to share)
        # We create one per camera task to avoid contention.
        self._detector = cv2.FaceDetectorYN.create(
            model=model_path,
            config="",
            input_size=(320, 320),
            score_threshold=0.6,
            nms_threshold=0.3,
            top_k=5,
        )
        self._lock = asyncio.Lock()  # single detector per camera, serialise calls

    def _detect_sync(self, frame: np.ndarray) -> np.ndarray | None:
        h, w = frame.shape[:2]
        self._detector.setInputSize((w, h))
        _, faces = self._detector.detect(frame)
        return faces  # None or ndarray of shape (N, 15)

    async def detect(self, frame: np.ndarray) -> list[np.ndarray]:
        """
        Returns list of face rows (each row: [x, y, w, h, landmarks..., score]).
        """
        loop = asyncio.get_event_loop()
        async with self._lock:
            faces = await loop.run_in_executor(self._executor, self._detect_sync, frame)

        if faces is None:
            return []
        return [faces[i] for i in range(faces.shape[0])]
