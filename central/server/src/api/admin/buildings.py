from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError

from core.dependencies import AdminDep, DbDep
from models.building import Building
from models.room import Room
from schemas.room import RoomCreate, RoomResponse
from schemas.building import BuildingCreate, BuildingResponse, BuildingUpdate

router = APIRouter(prefix="/buildings", tags=["Buildings"])


@router.get("", response_model=list[BuildingResponse])
async def get_buildings(db: DbDep, _admin: AdminDep):
    result = await db.execute(select(Building).order_by(Building.name))
    return result.scalars().all()


@router.post("", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED)
async def create_building(body: BuildingCreate, db: DbDep, _admin: AdminDep):
    building = Building(**body.model_dump())
    db.add(building)
    try:
        await db.commit()
        await db.refresh(building)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"Building '{body.name}' already exists")
    return building


@router.delete("/{building_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_building(building_id: int, db: DbDep, _admin: AdminDep):
    try:
        result = await db.execute(delete(Building).where(Building.id == building_id))
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Building not found")
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Building is used by other entities")


@router.patch("/{building_id}", response_model=BuildingResponse)
async def update_building(building_id: int, body: BuildingUpdate, db: DbDep, _admin: AdminDep):
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No fields to update")
    try:
        result = await db.execute(
            update(Building)
            .where(Building.id == building_id)
            .values(**data)
            .returning(Building)
        )
        building = result.scalar_one_or_none()
        if building is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Building not found")
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Building with this name already exists")
    return building


# --- Rooms ---

@router.get("/{building_id}/rooms", response_model=list[RoomResponse])
async def get_rooms(building_id: int, db: DbDep, _admin: AdminDep):
    building = await db.get(Building, building_id)
    if not building:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Building not found")
    result = await db.execute(
        select(Room).where(Room.building_id == building_id).order_by(Room.name)
    )
    return result.scalars().all()


@router.post("/{building_id}/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(building_id: int, body: RoomCreate, db: DbDep, _admin: AdminDep):
    building = await db.get(Building, building_id)
    if not building:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Building not found")
    room = Room(**body.model_dump(), building_id=building_id)
    db.add(room)
    try:
        await db.commit()
        await db.refresh(room)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"Room '{body.name}' already exists in this building")
    return room


# @router.post("/bulk", response_model=list[BuildingResponse], status_code=status.HTTP_201_CREATED)
# async def create_buildings_bulk(body: list[BuildingCreate], db: DbDep, _admin: AdminDep):
#     buildings_data = [item.model_dump() for item in body]

#     stmt = insert(Building).returning(Building)
#     try:
#         result = await db.scalars(stmt.values(buildings_data))
#         created_buildings = result.all()
#         await db.commit()
#         return created_buildings
#     except IntegrityError:
#         await db.rollback()
#         raise HTTPException(
#             status.HTTP_409_CONFLICT,
#             "One or more buildings already exist."
#         )