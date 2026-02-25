from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete, func

from core.dependencies import AdminDep, DbDep
from models.room import Room
from models.person import Person
from models.session import Session, SessionMember
from schemas.session import (
    SessionCreate,
    SessionResponse,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("", response_model=list[SessionResponse])
async def get_sessions(db: DbDep, _admin: AdminDep):
    members_count = (
        select(func.count())
        .where(SessionMember.session_id == Session.id)
        .correlate(Session)
        .scalar_subquery()
    )
    result = await db.execute(
        select(
            Session.id,
            Session.external_id,
            Session.subject,
            Session.room_id,
            Session.start_time,
            Session.end_time,
            members_count.label("members_count"),
        )
        .order_by(Session.start_time)
    )
    return [SessionResponse.model_validate(row._mapping) for row in result.all()]


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: int, db: DbDep, _admin: AdminDep):
    try:
        result = await db.execute(delete(Session).where(Session.id == session_id))
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Session is used by other entities")


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(body: SessionCreate, db: DbDep, _admin: AdminDep):
    room = await db.get(Room, body.room_id)
    if not room:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Room not found")

    result = await db.execute(select(Person.id).where(Person.id.in_(body.person_ids)))
    found_ids = set(result.scalars().all())
    missing = set(body.person_ids) - found_ids
    if missing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Persons not found: {missing}")

    session = Session(**body.model_dump(exclude={"person_ids"}))
    db.add(session)
    await db.flush()

    for person_id in body.person_ids:
        db.add(SessionMember(session_id=session.id, person_id=person_id))

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Session with this external_id already exists")

    return SessionResponse(
        id=session.id,
        external_id=session.external_id,
        room_id=session.room_id,
        subject=session.subject,
        start_time=session.start_time,
        end_time=session.end_time,
        members_count=len(body.person_ids),
    )


# @router.get("/{session_id}/attendance", response_model=SessionAttendanceResponse)
# async def get_session_attendance(session_id: int, db: DbDep, _admin: AdminDep):
#     session = await db.get(Session, session_id)
#     if session is None:
#         raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")

#     result = await db.execute(
#         select(AttendanceLog)
#         .where(AttendanceLog.session_id == session.id)
#         .options(selectinload(AttendanceLog.person))
#     )
#     logs = result.scalars().all()

#     attendance = [
#         AttendanceEntry(
#             person_id=log.person_id,
#             full_name=log.person.full_name,
#             person_code=log.person.person_code,
#             first_seen_at=log.first_seen_at,
#             last_seen_at=log.last_seen_at,
#             detection_count=log.detection_count,
#             max_confidence=log.max_confidence,
#         )
#         for log in logs
#     ]

#     return SessionAttendanceResponse(
#         session_id=session.id,
#         subject=session.subject,
#         start_time=session.start_time,
#         end_time=session.end_time,
#         attendance=attendance,
#     )


# @router.post("/bulk", response_model=SessionBulkResponse)
# async def import_sessions_bulk(body: SessionBulkImport, db: DbDep, _admin: AdminDep):
#     created = 0
#     updated = 0
#     errors = []

#     for s in body.sessions:
#         result = await db.execute(
#             select(Room)
#             .join(Building)
#             .where(Building.name == s.room.building, Room.name == s.room.name)
#         )
#         room = result.scalar_one_or_none()
#         if room is None:
#             errors.append(f"room '{s.room.building}/{s.room.name}' not found — session {s.external_id} rejected")
#             continue

#         person_ids = []
#         session_rejected = False
#         for code in s.student_codes:
#             result = await db.execute(
#                 select(Person).where(Person.person_code == code)
#             )
#             person = result.scalar_one_or_none()
#             if person is None:
#                 errors.append(f"student_code {code} not found — session {s.external_id} rejected")
#                 session_rejected = True
#                 break
#             person_ids.append(person.id)

#         if session_rejected:
#             continue

#         result = await db.execute(
#             select(Session).where(Session.external_id == s.external_id)
#         )
#         existing = result.scalar_one_or_none()

#         if existing:
#             existing.room_id = room.id
#             existing.subject = s.subject
#             existing.start_time = s.start_time
#             existing.end_time = s.end_time

#             await db.execute(
#                 SessionMember.__table__.delete().where(
#                     SessionMember.session_id == existing.id
#                 )
#             )
#             for pid in person_ids:
#                 db.add(SessionMember(session_id=existing.id, person_id=pid))
#             updated += 1
#         else:
#             session = Session(
#                 external_id=s.external_id,
#                 room_id=room.id,
#                 subject=s.subject,
#                 start_time=s.start_time,
#                 end_time=s.end_time,
#             )
#             db.add(session)
#             await db.flush()

#             for pid in person_ids:
#                 db.add(SessionMember(session_id=session.id, person_id=pid))
#             created += 1

#     await db.commit()
#     return SessionBulkResponse(created=created, updated=updated, errors=errors)