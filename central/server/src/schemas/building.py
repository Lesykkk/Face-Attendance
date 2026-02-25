from pydantic import BaseModel, ConfigDict, Field


class BuildingCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class BuildingUpdate(BaseModel):
    name: str = Field(default=None, min_length=1, max_length=50)


class BuildingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
