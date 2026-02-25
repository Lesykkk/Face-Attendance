from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, IntPKMixin

if TYPE_CHECKING:
    from models.face_embedding import FaceEmbedding


class PersonRole(enum.StrEnum):
    STUDENT = "student"
    TEACHER = "teacher"
    STAFF = "staff"


class Person(IntPKMixin, Base):
    __tablename__ = "persons"

    full_name: Mapped[str] = mapped_column(String(100))
    person_code: Mapped[str] = mapped_column(String(50), unique=True)
    role: Mapped[PersonRole] = mapped_column(Enum(PersonRole, name="person_role"))

    embeddings: Mapped[list[FaceEmbedding]] = relationship(back_populates="person", lazy="raise", passive_deletes=True)
