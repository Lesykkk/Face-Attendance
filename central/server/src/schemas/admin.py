from pydantic import BaseModel, ConfigDict, Field


class AdminCreate(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=5, max_length=128)


class AdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
