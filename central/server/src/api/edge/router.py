from datetime import datetime, timezone

from fastapi import APIRouter, status
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from core.dependencies import DbDep, EdgeNodeDep
from models.camera import Camera
from models.session import Session
from models.face_embedding import FaceEmbedding
from models.attendance_log import AttendanceLog
from schemas.edge import (
    EdgeAttendanceReport,
    EdgeSessionData,
    EdgeStudentEmbedding,
    EdgeSyncResponse,
)

router = APIRouter(prefix="/edge", tags=["Edge"])


@router.get("/sync", response_model=EdgeSyncResponse)
async def edge_sync(db: DbDep, edge_node: EdgeNodeDep):
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(Camera).where(
            Camera.edge_node_id == edge_node.id,
            Camera.is_active == True,
        )
    )
    cameras = result.scalars().all()

    if not cameras:
        return EdgeSyncResponse(sessions=[])

    sessions_data = []

    for camera in cameras:
        result = await db.execute(
            select(Session)
            .where(
                Session.room_id == camera.room_id,
                Session.start_time <= now,
                Session.end_time >= now,
            )
            .options(selectinload(Session.members))
        )
        active_sessions = result.scalars().all()

        for session in active_sessions:
            students = []
            for member in session.members:
                result = await db.execute(
                    select(FaceEmbedding).where(
                        FaceEmbedding.person_id == member.person_id
                    )
                )
                embeddings = result.scalars().all()

                if embeddings:
                    students.append(EdgeStudentEmbedding(
                        person_id=member.person_id,
                        embeddings=[
                            e.embedding.tolist() if hasattr(e.embedding, 'tolist') else list(e.embedding)
                            for e in embeddings
                        ],
                    ))

            sessions_data.append(EdgeSessionData(
                session_id=session.id,
                camera_rtsp=camera.rtsp_url,
                start_time=session.start_time,
                end_time=session.end_time,
                students=students,
            ))

    return EdgeSyncResponse(sessions=sessions_data)


@router.post("/attendance", status_code=status.HTTP_200_OK)
async def report_attendance(body: EdgeAttendanceReport, db: DbDep, edge_node: EdgeNodeDep):
    result = await db.execute(
        select(AttendanceLog).where(
            and_(
                AttendanceLog.person_id == body.person_id,
                AttendanceLog.session_id == body.session_id,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.last_seen_at = body.timestamp
        existing.detection_count += 1
        if body.confidence > existing.max_confidence:
            existing.max_confidence = body.confidence
    else:
        log = AttendanceLog(
            person_id=body.person_id,
            session_id=body.session_id,
            first_seen_at=body.timestamp,
            last_seen_at=body.timestamp,
            detection_count=1,
            max_confidence=body.confidence,
            edge_node_id=edge_node.id,
        )
        db.add(log)

    await db.commit()
    return {"status": "ok"}
