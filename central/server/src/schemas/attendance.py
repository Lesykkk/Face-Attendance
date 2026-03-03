from pydantic import BaseModel, ConfigDict


class AttendanceLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    person: str
    session: str 
    building: str
    room: str
    time: str
    confidence: str


class AttendanceResponse(BaseModel):
    logs: list[AttendanceLogResponse]
