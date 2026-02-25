"""
SFace face recognizer wrapper — aligns the detected face crop and extracts
a 128D embedding vector. Offloads to ThreadPoolExecutor.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class FaceEmbedder:
    def __init__(self, model_path: str, executor: ThreadPoolExecutor) -> None:
        self._executor = executor
        self._recognizer = cv2.FaceRecognizerSF.create(
            model=model_path,
            config="",
        )
        self._lock = asyncio.Lock()

    def _embed_sync(self, frame: np.ndarray, face: np.ndarray) -> np.ndarray:
        aligned = self._recognizer.alignCrop(frame, face)
        feature = self._recognizer.feature(aligned)
        # feature is shape (1, 128) — flatten and L2-normalize
        vec = feature.flatten()
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    async def embed(self, frame: np.ndarray, face: np.ndarray) -> np.ndarray:
        """Returns a normalized 128D float32 numpy array."""
        loop = asyncio.get_event_loop()
        async with self._lock:
            return await loop.run_in_executor(self._executor, self._embed_sync, frame, face)
