import secrets

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError

from core.dependencies import AdminDep, DbDep
from core.security import hash_api_key
from models.room import Room
from models.edge_node import EdgeNode
from models.camera import Camera
from schemas.hardware import(
    CameraCreate,
    CameraResponse,
    EdgeNodeCreate,
    EdgeNodeResponse,
    EdgeNodeResponseAfterCreate,
    EdgeNodeUpdate,
    CameraUpdate
)

router = APIRouter(prefix="/hardware", tags=["Hardware"])


# ── Edge Nodes ──

@router.get("/nodes", response_model=list[EdgeNodeResponse])
async def get_edge_nodes(db: DbDep, _admin: AdminDep):
    result = await db.execute(select(EdgeNode).order_by(EdgeNode.name))
    return result.scalars().all()


@router.post("/nodes", response_model=EdgeNodeResponseAfterCreate, status_code=status.HTTP_201_CREATED)
async def create_edge_node(body: EdgeNodeCreate, db: DbDep, _admin: AdminDep):
    api_key = secrets.token_hex(32)
    node = EdgeNode(
        **body.model_dump(),
        api_key_hash=hash_api_key(api_key),
    )
    db.add(node)
    try:
        await db.commit()
        await db.refresh(node)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"Edge node '{body.name}' already exists")

    return EdgeNodeResponseAfterCreate(id=node.id, name=node.name, api_key=api_key)


# ── Cameras ──

@router.get("/nodes/{node_id}/cameras", response_model=list[CameraResponse])
async def get_cameras(node_id: int, db: DbDep, _admin: AdminDep):
    result = await db.execute(select(Camera).where(Camera.edge_node_id == node_id))
    return result.scalars().all()


@router.post("/nodes/{node_id}/cameras", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(node_id: int, body: CameraCreate, db: DbDep, _admin: AdminDep):
    edge_node = await db.get(EdgeNode, node_id)
    if not edge_node:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Edge node not found")
    room = await db.get(Room, body.room_id)
    if not room:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Room not found")
    camera = Camera(**body.model_dump(), edge_node_id=node_id)
    db.add(camera)
    try:
        await db.commit()
        await db.refresh(camera)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Camera already exists")
    return camera



# ── Edge Nodes ──

@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_edge_node(node_id: int, db: DbDep, _admin: AdminDep):
    try:
        result = await db.execute(delete(EdgeNode).where(EdgeNode.id == node_id))
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Edge node not found")
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Edge node is used by other entities")


@router.patch("/nodes/{node_id}", response_model=EdgeNodeResponse)
async def update_edge_node(node_id: int, body: EdgeNodeUpdate, db: DbDep, _admin: AdminDep):
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No fields to update")
    try:
        result = await db.execute(
            update(EdgeNode)
            .where(EdgeNode.id == node_id)
            .values(**data)
            .returning(EdgeNode)
        )
        node = result.scalar_one_or_none()
        if node is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Edge node not found")
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Edge node with this name already exists")
    return node


# ── Cameras ──

@router.delete("/cameras/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(camera_id: int, db: DbDep, _admin: AdminDep):
    try:
        result = await db.execute(delete(Camera).where(Camera.id == camera_id))
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Camera not found")
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Camera is used by other entities")


@router.patch("/cameras/{camera_id}", response_model=CameraResponse)
async def update_camera(camera_id: int, body: CameraUpdate, db: DbDep, _admin: AdminDep):
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No fields to update")
    try:
        result = await db.execute(
            update(Camera)
            .where(Camera.id == camera_id)
            .values(**data)
            .returning(Camera)
        )
        camera = result.scalar_one_or_none()
        if camera is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Camera not found")
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Camera already exists")
    return camera