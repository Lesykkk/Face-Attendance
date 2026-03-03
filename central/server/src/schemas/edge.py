from datetime import datetime

from pydantic import BaseModel


class EdgeStudentEmbedding(BaseModel):
    person_id: int
    embeddings: list[list[float]]


class EdgeSessionData(BaseModel):
    session_id: int
    camera_id: int
    camera_rtsp: str
    start_time: datetime
    end_time: datetime
    students: list[EdgeStudentEmbedding]


class EdgeSyncResponse(BaseModel):
    sessions: list[EdgeSessionData]


class EdgeAttendanceReport(BaseModel):
    person_id: int
    session_id: int
    timestamp: datetime
    confidence: float
