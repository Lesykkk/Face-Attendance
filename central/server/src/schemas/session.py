from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    external_id: str = Field(min_length=1, max_length=100)
    room_id: int
    subject: str = Field(min_length=1, max_length=255)
    start_time: datetime
    end_time: datetime
    person_ids: list[int] = Field(min_length=1)


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    room_id: int
    subject: str
    start_time: datetime
    end_time: datetime
    members_count: int




# from datetime import datetime

# from pydantic import BaseModel, ConfigDict, Field


# class SessionRoom(BaseModel):
#     building: str = Field(min_length=1, max_length=50)
#     name: str = Field(min_length=1, max_length=50)


# class SessionCreate(BaseModel):
#     external_id: str = Field(min_length=1, max_length=100)
#     room: SessionRoom
#     subject: str = Field(min_length=1, max_length=255)
#     start_time: datetime
#     end_time: datetime
#     student_codes: list[str]


# class SessionBulkImport(BaseModel):
#     date: str
#     sessions: list[SessionCreate]


# class SessionBulkResponse(BaseModel):
#     created: int
#     updated: int
#     errors: list[str]


# class SessionResponse(BaseModel):
#     id: int
#     external_id: str
#     subject: str
#     room: str | None = None
#     building: str | None = None
#     start_time: datetime
#     end_time: datetime
#     members_count: int


# class AttendanceEntry(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

#     person_id: int
#     full_name: str
#     person_code: str
#     first_seen_at: datetime
#     last_seen_at: datetime
#     detection_count: int
#     max_confidence: float


# class SessionAttendanceResponse(BaseModel):
#     session_id: int
#     subject: str
#     start_time: datetime
#     end_time: datetime
#     attendance: list[AttendanceEntry]
