from pydantic import BaseModel, ConfigDict


class RecentLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    person: str
    building: str
    room: str
    subject: str
    time: str
    confidence: str


class DashboardStatsResponse(BaseModel):
    totalStudents: str
    activeNodes: str
    attendanceToday: str
    ongoingSessions: str
    recentLogs: list[RecentLogResponse]
