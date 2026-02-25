from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.person import Person
    from models.session import Session
    from models.edge_node import EdgeNode


class AttendanceLog(Base):
    __tablename__ = "attendance_logs"
    __table_args__ = (
        UniqueConstraint("person_id", "session_id", name="uq_attendance_person_session"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("persons.id"))
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sessions.id"))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    detection_count: Mapped[int] = mapped_column(Integer, default=1)
    max_confidence: Mapped[float] = mapped_column(Float)
    edge_node_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("edge_nodes.id"))

    person: Mapped[Person] = relationship(lazy="raise")
    session: Mapped[Session] = relationship(lazy="raise")
    edge_node: Mapped[EdgeNode] = relationship(lazy="raise")
