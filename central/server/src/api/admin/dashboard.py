from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from core.dependencies import AdminDep, DbDep
from core.tunnel_registry import registry as tunnel_registry
from models.attendance_log import AttendanceLog
from models.edge_node import EdgeNode
from models.person import Person, PersonRole
from models.session import Session, SessionMember
from models.room import Room
from schemas.dashboard import DashboardStatsResponse, RecentLogResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: DbDep, _admin: AdminDep):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # 1. Total Students
    result = await db.execute(select(func.count(Person.id)).where(Person.role == PersonRole.STUDENT))
    total_students = result.scalar_one()

    # 2. Active Nodes
    result = await db.execute(select(func.count(EdgeNode.id)))
    total_nodes = result.scalar_one()
    active_nodes = sum(1 for node_id in tunnel_registry._tunnels.keys())
    nodes_str = f"{active_nodes}/{total_nodes}"

    # 3. Ongoing Sessions
    result = await db.execute(
        select(func.count(Session.id)).where(
            Session.start_time <= now,
            Session.end_time >= now,
        )
    )
    ongoing_sessions = result.scalar_one()

    # 4. Attendance Today
    result = await db.execute(
        select(Session.id).where(
            Session.start_time >= today_start,
            Session.start_time <= today_end,
        )
    )
    today_session_ids = result.scalars().all()

    attendance_pct = "0%"
    if today_session_ids:
        # Expected attendance: sum of SessionMembers for today's sessions
        result = await db.execute(
            select(func.count(SessionMember.person_id)).where(
                SessionMember.session_id.in_(today_session_ids)
            )
        )
        expected_attendance = result.scalar_one()

        actual_attendance = 0
        if expected_attendance > 0:
            # Actual attendance: count of unique (person_id, session_id) in AttendanceLog for today's sessions
            result = await db.execute(
                select(func.count(AttendanceLog.id)).where(
                    AttendanceLog.session_id.in_(today_session_ids)
                )
            )
            actual_attendance = result.scalar_one()

            # Prevent division by zero just in case
            if expected_attendance > 0:
                pct = int((actual_attendance / expected_attendance) * 100)
                attendance_pct = f"{pct}%"

    # 5. Recent Logs
    result = await db.execute(
        select(AttendanceLog)
        .options(
            joinedload(AttendanceLog.person),
            joinedload(AttendanceLog.session).joinedload(Session.room).joinedload(Room.building)
        )
        .order_by(AttendanceLog.last_seen_at.desc())
        .limit(5)
    )
    recent_logs_orm = result.scalars().all()

    recent_logs = []
    for log in recent_logs_orm:
        if not log.person or not log.session or not log.session.room:
            continue

        recent_logs.append(
            RecentLogResponse(
                id=log.id,
                person=log.person.full_name,
                building=log.session.room.building.name,
                room=log.session.room.name,
                subject=log.session.subject,
                time=log.last_seen_at.isoformat(),
                confidence=f"{int(log.max_confidence * 100)}%"
            )
        )

    return DashboardStatsResponse(
        totalStudents=f"{total_students:,}",
        activeNodes=nodes_str,
        attendanceToday=attendance_pct,
        ongoingSessions=str(ongoing_sessions),
        recentLogs=recent_logs
    )
