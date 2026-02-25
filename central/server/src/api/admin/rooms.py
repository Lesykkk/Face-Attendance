from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError

from core.dependencies import AdminDep, DbDep
from models.room import Room
from schemas.room import RoomUpdate, RoomResponse

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(room_id: int, db: DbDep, _admin: AdminDep):
    try:
        result = await db.execute(delete(Room).where(Room.id == room_id))
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Room not found")
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Room is used by other entities")


@router.patch("/{room_id}", response_model=RoomResponse)
async def update_room(room_id: int, body: RoomUpdate, db: DbDep, _admin: AdminDep):
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No fields to update")
    try:
        result = await db.execute(
            update(Room)
            .where(Room.id == room_id)
            .values(**data)
            .returning(Room)
        )
        room = result.scalar_one_or_none()
        if room is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Room not found")
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Room already exists in this building")
    return room


# @router.post("/bulk", response_model=list[RoomResponse], status_code=status.HTTP_201_CREATED)
# async def create_rooms_bulk(body: list[RoomCreate], db: DbDep, _admin: AdminDep):
#     created = []
#     for item in body:
#         room = Room(**item.model_dump())
#         db.add(room)
#         try:
#             await db.flush()
#             await db.refresh(room)
#             created.append(room)
#         except IntegrityError:
#             await db.rollback()
#             raise HTTPException(
#                 status.HTTP_409_CONFLICT,
#                 f"Room '{item.name}' already exists in building '{item.building_id}'",
#             )
#     await db.commit()
#     return created
