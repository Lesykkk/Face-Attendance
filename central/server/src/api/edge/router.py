from datetime import datetime, timezone

from fastapi import APIRouter, status
from sqlalchemy import select, and_, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload

from core.dependencies import DbDep, EdgeNodeDep
from models.camera import Camera
from models.person import Person
from models.session import Session, SessionMember
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

    room_ids = [c.room_id for c in cameras]

    result = await db.execute(
        select(Session)
        .where(
            Session.room_id.in_(room_ids),
            Session.start_time <= now,
            Session.end_time >= now,
        )
        .options(
            selectinload(Session.members)
            .selectinload(SessionMember.person)
            .selectinload(Person.embeddings)
        )
    )
    active_sessions = result.scalars().all()

    if not active_sessions:
        return EdgeSyncResponse(sessions=[])

    room_to_cameras: dict[int, list] = {}
    for c in cameras:
        room_to_cameras.setdefault(c.room_id, []).append(c)

    sessions_data = []
    for session in active_sessions:
        cams = room_to_cameras.get(session.room_id, [])
        if not cams:
            continue

        students = [
            EdgeStudentEmbedding(
                person_id=member.person_id,
                embeddings=[list(e.embedding) for e in member.person.embeddings],
            )
            for member in session.members if member.person.embeddings
        ]

        for camera in cams:
            sessions_data.append(EdgeSessionData(
                session_id=session.id,
                camera_id=camera.id,
                camera_rtsp=camera.rtsp_url,
                start_time=session.start_time,
                end_time=session.end_time,
                students=students,
            ))

    return EdgeSyncResponse(sessions=sessions_data)


@router.post("/attendance", status_code=status.HTTP_200_OK)
async def report_attendance(body: EdgeAttendanceReport, db: DbDep, edge_node: EdgeNodeDep):
    stmt = (
        pg_insert(AttendanceLog)
        .values(
            person_id=body.person_id,
            session_id=body.session_id,
            first_seen_at=body.timestamp,
            last_seen_at=body.timestamp,
            detection_count=1,
            max_confidence=body.confidence,
            edge_node_id=edge_node.id,
        )
        .on_conflict_do_update(
            index_elements=["person_id", "session_id"],
            set_={
                "last_seen_at": body.timestamp,
                "detection_count": AttendanceLog.detection_count + 1,
                "max_confidence": func.greatest(
                    AttendanceLog.max_confidence, body.confidence
                ),
            },
        )
    )
    await db.execute(stmt)
    await db.commit()
    return {"status": "ok"}
