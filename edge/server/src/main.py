"""
Edge Node entry point — asyncio orchestrator.

Startup sequence:
1. Start SyncManager background task
2. Wait for first successful sync
3. Spawn one camera pipeline task per unique RTSP camera URL
4. On subsequent syncs the camera list may change — tasks are restarted if needed

Pipeline per camera (indefinite loop):
  grab frame → skip Nth → detect faces → embed each face → match → cooldown → report
"""

import asyncio
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from config import settings
from pipeline.detector import FaceDetector
from pipeline.embedder import FaceEmbedder
from pipeline.grabber import FrameGrabber
from pipeline.matcher import CooldownFilter, Matcher
from pipeline.reporter import AttendanceReporter
from sync.sync_manager import SyncManager, SyncState

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logging.getLogger("pipeline.matcher").setLevel(logging.DEBUG)
logger = logging.getLogger("edge.main")


async def camera_pipeline(
    rtsp_url: str,
    executor: ThreadPoolExecutor,
    sync_manager: SyncManager,
    reporter: AttendanceReporter,
) -> None:
    """Infinite pipeline loop for a single camera."""
    detector = FaceDetector(settings.yunet_model_path, executor)
    embedder = FaceEmbedder(settings.sface_model_path, executor)
    matcher = Matcher(settings.detection_threshold)
    cooldown = CooldownFilter(settings.attendance_cooldown_minutes)
    grabber = FrameGrabber(rtsp_url, executor)

    grabber.start()
    logger.info(f"[Pipeline] Started camera: {rtsp_url}")

    frame_counter = 0

    try:
        async for frame in grabber.frames():
            frame_counter += 1

            # Skip frames according to FRAME_SKIP
            if frame_counter % settings.frame_skip != 0:
                continue

            # Get current active sessions for this camera
            state: SyncState = await sync_manager.get_state()
            sessions = state.camera_sessions.get(rtsp_url, [])

            if not sessions:
                continue  # no active sessions for this camera right now

            # Detect faces
            faces = await detector.detect(frame)
            logger.info(f"[Pipeline] Frame #{frame_counter}: {len(faces)} face(s) detected")
            if not faces:
                continue

            now = datetime.now(timezone.utc)
            matched_count = 0

            for face in faces:
                # Embed each detected face
                embedding = await embedder.embed(frame, face)

                # Try to match against all active sessions
                for session in sessions:
                    result = matcher.find_match(embedding, session.students)
                    if result is None:
                        continue

                    person_id, confidence = result

                    if not cooldown.should_report(person_id, session.session_id):
                        matched_count += 1
                        continue

                    # Report to Central Server
                    await reporter.report(person_id, session.session_id, now, confidence)
                    cooldown.mark_reported(person_id, session.session_id)
                    matched_count += 1

            if matched_count:
                logger.info(f"[Pipeline] Frame #{frame_counter}: {matched_count}/{len(faces)} face(s) matched")

    except asyncio.CancelledError:
        logger.info(f"[Pipeline] Camera task cancelled: {rtsp_url}")
    finally:
        grabber.stop()


async def main() -> None:
    reporter = AttendanceReporter(settings.central_server_url, settings.edge_api_key)
    sync_manager = SyncManager(
        settings.central_server_url,
        settings.edge_api_key,
        settings.sync_interval_seconds,
    )

    executor = ThreadPoolExecutor(max_workers=settings.cv_workers)

    # Start background sync
    sync_task = asyncio.create_task(sync_manager.run(), name="sync_manager")

    logger.info("[Main] Waiting for first sync...")
    await sync_manager.wait_for_first_sync()

    state = await sync_manager.get_state()
    rtsp_urls = list(state.camera_sessions.keys())

    if not rtsp_urls:
        logger.warning("[Main] No active sessions found after sync. Keeping sync running and waiting...")

    camera_tasks: dict[str, asyncio.Task] = {}

    async def spawn_camera_tasks(urls: list[str]) -> None:
        for url in urls:
            if url not in camera_tasks or camera_tasks[url].done():
                task = asyncio.create_task(
                    camera_pipeline(url, executor, sync_manager, reporter),
                    name=f"camera_{url}",
                )
                camera_tasks[url] = task
                logger.info(f"[Main] Spawned task for camera: {url}")

    await spawn_camera_tasks(rtsp_urls)

    # Periodically check if new cameras appeared after a re-sync
    async def watch_loop() -> None:
        while True:
            await asyncio.sleep(settings.sync_interval_seconds)
            new_state = await sync_manager.get_state()
            new_urls = list(new_state.camera_sessions.keys())
            await spawn_camera_tasks(new_urls)

    watch_task = asyncio.create_task(watch_loop(), name="watch_loop")

    try:
        await asyncio.gather(sync_task, watch_task, *camera_tasks.values())
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("[Main] Shutting down...")
        for task in camera_tasks.values():
            task.cancel()
        sync_task.cancel()
        watch_task.cancel()
        await reporter.aclose()
        await sync_manager.aclose()
        executor.shutdown(wait=False)
        logger.info("[Main] Shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
