"""
RTSP Frame Grabber — async, per-camera, with exponential backoff reconnect.

Captures frames in a background thread (blocking cv2 I/O) and feeds them
into an asyncio.Queue. The queue holds at most 2 frames; older frames are
dropped when full so the pipeline always sees the freshest image.
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_BACKOFF_INITIAL = 1.0
_BACKOFF_MAX = 60.0


def _open_capture(rtsp_url: str) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def _grab_loop(rtsp_url: str, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop, stop_event: asyncio.Event) -> None:
    """Runs in a thread. Reads frames and puts them on the asyncio queue."""
    backoff = _BACKOFF_INITIAL
    cap = None

    while not stop_event.is_set():
        if cap is None or not cap.isOpened():
            logger.info(f"[Grabber] Connecting to {rtsp_url} ...")
            cap = _open_capture(rtsp_url)
            if not cap.isOpened():
                logger.warning(f"[Grabber] Failed to open {rtsp_url}. Retry in {backoff:.0f}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, _BACKOFF_MAX)
                cap = None
                continue
            logger.info(f"[Grabber] Connected to {rtsp_url}")
            backoff = _BACKOFF_INITIAL

        ok, frame = cap.read()
        if not ok:
            logger.warning(f"[Grabber] Lost stream {rtsp_url}. Reconnecting in {backoff:.0f}s")
            cap.release()
            cap = None
            time.sleep(backoff)
            backoff = min(backoff * 2, _BACKOFF_MAX)
            continue

        # Drop oldest if queue is full (non-blocking put)
        if queue.full():
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass

        # Thread-safe put into asyncio queue
        asyncio.run_coroutine_threadsafe(queue.put(frame), loop)

    if cap and cap.isOpened():
        cap.release()
    logger.info(f"[Grabber] Stopped for {rtsp_url}")


class FrameGrabber:
    """
    Manages a background thread that continuously grabs frames from an RTSP stream.
    Provides an async generator interface for consuming frames.
    """

    def __init__(self, rtsp_url: str, executor: ThreadPoolExecutor) -> None:
        self.rtsp_url = rtsp_url
        self._executor = executor
        self._queue: asyncio.Queue[np.ndarray] = asyncio.Queue(maxsize=2)
        self._stop_event: asyncio.Event | None = None
        self._thread_future = None

    def start(self) -> None:
        loop = asyncio.get_event_loop()
        self._stop_event = asyncio.Event()
        self._thread_future = self._executor.submit(
            _grab_loop, self.rtsp_url, self._queue, loop, self._stop_event
        )

    def stop(self) -> None:
        if self._stop_event:
            self._stop_event.set()

    async def frames(self):
        """Async generator that yields frames as they arrive."""
        while True:
            frame = await self._queue.get()
            yield frame
