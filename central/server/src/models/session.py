from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, IntPKMixin

if TYPE_CHECKING:
    from models.room import Room
    from models.person import Person


class Session(IntPKMixin, Base):
    __tablename__ = "sessions"

    external_id: Mapped[str] = mapped_column(String(100), unique=True)
    room_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rooms.id"))
    subject: Mapped[str] = mapped_column(String(255))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    room: Mapped[Room] = relationship(lazy="raise")
    members: Mapped[list[SessionMember]] = relationship(back_populates="session", lazy="raise")


class SessionMember(Base):
    __tablename__ = "session_members"

    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True
    )
    person_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True
    )

    session: Mapped[Session] = relationship(back_populates="members", lazy="raise")
    person: Mapped[Person] = relationship(lazy="raise")