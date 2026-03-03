from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from core.dependencies import AdminDep, DbDep
from models.attendance_log import AttendanceLog
from models.session import Session
from models.room import Room
from schemas.attendance import AttendanceLogResponse, AttendanceResponse

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("", response_model=AttendanceResponse)
async def get_all_attendance_logs(db: DbDep, _admin: AdminDep):
    result = await db.execute(
        select(AttendanceLog)
        .options(
            joinedload(AttendanceLog.person),
            joinedload(AttendanceLog.session).joinedload(Session.room).joinedload(Room.building)
        )
        .order_by(AttendanceLog.last_seen_at.desc())
    )
    logs_orm = result.scalars().all()

    formatted_logs = []
    for log in logs_orm:
        if not log.person or not log.session or not log.session.room:
            continue

        formatted_logs.append(
            AttendanceLogResponse(
                id=log.id,
                person=log.person.full_name,
                session=log.session.subject,
                building=log.session.room.building.name,
                room=log.session.room.name,
                time=log.last_seen_at.isoformat(),
                confidence=f"{int(log.max_confidence * 100)}%"
            )
        )

    return AttendanceResponse(logs=formatted_logs)
