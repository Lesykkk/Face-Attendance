from pydantic import BaseModel, ConfigDict, Field

from models.person import PersonRole


class PersonRegister(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    person_code: str = Field(min_length=1, max_length=50)
    role: PersonRole
    photos: list[str] = Field(min_length=1, max_length=10)


class PersonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    person_code: str
    role: PersonRole


class PersonUpdate(BaseModel):
    full_name: str = Field(default=None, min_length=1, max_length=100)
    person_code: str = Field(default=None, min_length=1, max_length=50)
    role: PersonRole = None