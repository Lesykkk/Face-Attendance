from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class RoomUpdate(BaseModel):
    name: str = Field(default=None, min_length=1, max_length=50)


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    building_id: int
    name: str
