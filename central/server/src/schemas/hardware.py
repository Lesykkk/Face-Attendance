from pydantic import BaseModel, ConfigDict, Field


class EdgeNodeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class EdgeNodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class EdgeNodeResponseAfterCreate(EdgeNodeResponse):
    api_key: str


class CameraCreate(BaseModel):
    room_id: int
    rtsp_url: str = Field(min_length=1, max_length=255)


class CameraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    edge_node_id: int
    rtsp_url: str
    is_active: bool


class EdgeNodeUpdate(BaseModel):
    name: str = Field(default=None, min_length=1, max_length=100)


class CameraUpdate(BaseModel):
    rtsp_url: str = Field(default=None, min_length=1, max_length=255)