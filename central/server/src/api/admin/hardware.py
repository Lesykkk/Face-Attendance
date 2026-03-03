import asyncio
import secrets
import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from core.dependencies import AdminDep, DbDep
from core.security import hash_api_key
from core.tunnel_registry import registry as tunnel_registry
from models.building import Building
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
    result = await db.execute(
        select(EdgeNode)
        .options(selectinload(EdgeNode.building))
        .order_by(EdgeNode.name)
    )
    return result.scalars().all()


@router.get("/nodes/status")
async def get_nodes_status(db: DbDep, _admin: AdminDep):
    """Returns online/offline status for all Edge Nodes based on active WebSocket tunnels."""
    result = await db.execute(select(EdgeNode.id))
    node_ids = result.scalars().all()
    return {node_id: tunnel_registry.is_online(node_id) for node_id in node_ids}


@router.post("/nodes", response_model=EdgeNodeResponseAfterCreate, status_code=status.HTTP_201_CREATED)
async def create_edge_node(body: EdgeNodeCreate, db: DbDep, _admin: AdminDep):
    building = await db.get(Building, body.building_id)
    if building is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Building not found")

    api_key = secrets.token_hex(32)
    node = EdgeNode(
        **body.model_dump(),
        api_key_hash=hash_api_key(api_key),
    )
    db.add(node)
    try:
        await db.commit()
        await db.refresh(node, attribute_names=["building"])
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"Edge node '{body.name}' already exists")

    return EdgeNodeResponseAfterCreate(
        id=node.id, name=node.name, building_id=node.building_id,
        building=node.building, api_key=api_key
    )


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
        )
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Edge node not found")
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Edge node with this name already exists")

    result = await db.execute(
        select(EdgeNode)
        .where(EdgeNode.id == node_id)
        .options(selectinload(EdgeNode.building))
    )
    return result.scalar_one()


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


# ── Camera Preview (Reverse WebSocket Tunnel) ──

_MJPEG_BOUNDARY = b"frame"
_MJPEG_CONTENT_TYPE = f"multipart/x-mixed-replace; boundary={_MJPEG_BOUNDARY.decode()}"


@router.get("/cameras/{camera_id}/preview")
async def preview_camera(camera_id: int, db: DbDep, _admin: AdminDep):
    """Stream live MJPEG preview from a camera via the Edge Node reverse tunnel."""
    camera = await db.get(Camera, camera_id)
    if camera is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Camera not found")

    node_id = camera.edge_node_id

    # Check tunnel is active
    if not tunnel_registry.is_online(node_id):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Edge Node is offline or not connected"
        )

    stream_id = str(uuid.uuid4())
    frame_queue = tunnel_registry.create_stream(stream_id)

    # Tell Edge Node to start streaming this camera
    sent = await tunnel_registry.send_command(node_id, {
        "type": "start_stream",
        "camera_id": camera_id,
        "stream_id": stream_id,
    })
    if not sent:
        tunnel_registry.close_stream(stream_id)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Failed to reach Edge Node")

    async def generate():
        try:
            while True:
                try:
                    jpeg = await asyncio.wait_for(frame_queue.get(), timeout=10.0)
                except asyncio.TimeoutError:
                    break

                if jpeg is None:
                    break

                yield (
                    b"--" + _MJPEG_BOUNDARY + b"\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + jpeg
                    + b"\r\n"
                )
        finally:
            await tunnel_registry.send_command(node_id, {
                "type": "stop_stream",
                "stream_id": stream_id,
            })
            tunnel_registry.close_stream(stream_id)

    return StreamingResponse(generate(), media_type=_MJPEG_CONTENT_TYPE)
