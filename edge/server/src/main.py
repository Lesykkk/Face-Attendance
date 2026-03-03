"""
Edge Node entry point — asyncio orchestrator.

Startup sequence:
1. Start SyncManager background task
2. Wait for first successful sync
3. Spawn one camera pipeline task per unique RTSP camera URL
4. Start TunnelClient — persistent WebSocket to Central Server for preview streaming
5. On subsequent syncs the camera list may change — tasks are restarted if needed

Pipeline per camera (indefinite loop):
  grab frame → skip Nth → publish to FrameRegistry → detect faces → embed → match → cooldown → report
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
from tunnel.frame_registry import FaceDetectionResult, registry as frame_registry
from tunnel.tunnel_client import TunnelClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logging.getLogger("pipeline.matcher").setLevel(logging.DEBUG)
logger = logging.getLogger("edge.main")


async def camera_pipeline(
    rtsp_url: str,
    camera_id: int,
    executor: ThreadPoolExecutor,
    sync_manager: SyncManager,
    reporter: AttendanceReporter,
) -> None:
    """Infinite pipeline loop for a single camera."""
    detector = FaceDetector(settings.YUNET_MODEL_PATH, executor,
                             top_k=settings.TOP_K,
                             score_threshold=settings.SCORE_THRESHOLD,
                             nms_threshold=settings.NMS_THRESHOLD)
    embedder = FaceEmbedder(settings.SFACE_MODEL_PATH, executor)
    matcher = Matcher(settings.DETECTION_THRESHOLD)
    cooldown = CooldownFilter(settings.ATTENDANCE_COOLDOWN_MINUTES)
    grabber = FrameGrabber(rtsp_url, executor)

    grabber.start()
    logger.info(f"[Pipeline] Started camera: {rtsp_url}")

    frame_counter = 0

    # Ensure registry has a queue for this camera
    frame_registry.register(camera_id)

    try:
        async for frame in grabber.frames():
            frame_counter += 1

            # Publish raw BGR frame to the preview registry (before frame_skip).
            # FrameRegistry handles JPEG encoding and overlay drawing internally.
            frame_registry.publish(camera_id, frame)

            # Skip frames according to FRAME_SKIP for face detection
            if frame_counter % settings.FRAME_SKIP != 0:
                continue

            # Get current active sessions for this camera
            state: SyncState = await sync_manager.get_state()
            sessions = state.camera_sessions.get(rtsp_url, [])

            # Periodically clean up cooldown entries for expired sessions
            if frame_counter % (settings.FRAME_SKIP * 100) == 0:
                active_ids = {s.session_id for s in sessions}
                cooldown.cleanup(active_ids)

            # Detect faces
            faces = await detector.detect(frame)
            logger.info(f"[Pipeline] Frame #{frame_counter}: {len(faces)} face(s) detected")

            if not faces:
                # Clear overlays when no faces in frame
                frame_registry.set_detections(camera_id, [])
                continue

            now = datetime.now(timezone.utc)
            matched_count = 0
            # Build per-face results: embed + match each face across all sessions
            face_results: list[FaceDetectionResult] = []

            for face in faces:
                embedding = await embedder.embed(frame, face)
                best_score: float | None = None

                for session in sessions:
                    result = matcher.find_match(embedding, session.students)
                    if result is None:
                        continue

                    person_id, confidence = result
                    # Keep the highest score across sessions for this face
                    if best_score is None or confidence > best_score:
                        best_score = confidence

                    if not cooldown.should_report(person_id, session.session_id):
                        matched_count += 1
                        continue

                    await reporter.report(person_id, session.session_id, now, confidence)
                    cooldown.mark_reported(person_id, session.session_id)
                    matched_count += 1

                face_results.append(FaceDetectionResult(face_row=face, match_score=best_score))

            # Update overlays: green+score for recognized, yellow+? for unknown
            frame_registry.set_detections(camera_id, face_results)

            if matched_count:
                logger.info(f"[Pipeline] Frame #{frame_counter}: {matched_count}/{len(faces)} face(s) matched")

    except asyncio.CancelledError:
        logger.info(f"[Pipeline] Camera task cancelled: {rtsp_url}")
    finally:
        grabber.stop()


async def main() -> None:
    reporter = AttendanceReporter(settings.CENTRAL_SERVER_URL, settings.EDGE_API_KEY)
    sync_manager = SyncManager(
        settings.CENTRAL_SERVER_URL,
        settings.EDGE_API_KEY,
        settings.SYNC_INTERVAL_SECONDS,
    )
    tunnel = TunnelClient(settings.CENTRAL_SERVER_URL, settings.EDGE_API_KEY)

    executor = ThreadPoolExecutor(max_workers=settings.CV_WORKERS)

    # Start background sync and tunnel
    sync_task = asyncio.create_task(sync_manager.run(), name="sync_manager")
    tunnel_task = asyncio.create_task(tunnel.run(), name="tunnel_client")

    logger.info("[Main] Waiting for first sync...")
    await sync_manager.wait_for_first_sync()

    # rtsp_url → asyncio.Task
    camera_tasks: dict[str, asyncio.Task] = {}

    async def reconcile_cameras() -> None:
        """Spawn new camera tasks and cancel stale ones based on current sync state."""
        state = await sync_manager.get_state()
        active_urls = set(state.camera_sessions.keys())

        # Cancel tasks for cameras that are no longer in sync
        stale_urls = set(camera_tasks.keys()) - active_urls
        for url in stale_urls:
            task = camera_tasks.pop(url)
            task.cancel()
            logger.info(f"[Main] Cancelled stale camera task: {url}")

        # Spawn tasks for new cameras (or ones that crashed)
        for url in active_urls:
            if url not in camera_tasks or camera_tasks[url].done():
                cam_id = state.camera_ids.get(url, abs(hash(url)) % (10 ** 9))
                task = asyncio.create_task(
                    camera_pipeline(url, cam_id, executor, sync_manager, reporter),
                    name=f"camera_{url}",
                )
                camera_tasks[url] = task
                logger.info(f"[Main] Spawned task for camera: {url} (camera_id={cam_id})")

    # Initial camera spawn
    await reconcile_cameras()

    # Periodically reconcile cameras after each sync cycle
    async def watch_loop() -> None:
        while True:
            await asyncio.sleep(settings.SYNC_INTERVAL_SECONDS)
            await reconcile_cameras()

    watch_task = asyncio.create_task(watch_loop(), name="watch_loop")

    try:
        # Only await the long-lived management tasks — camera tasks are
        # managed dynamically by watch_loop and don't need to be in gather.
        await asyncio.gather(sync_task, tunnel_task, watch_task)
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("[Main] Shutting down...")
        for task in camera_tasks.values():
            task.cancel()
        sync_task.cancel()
        tunnel_task.cancel()
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
