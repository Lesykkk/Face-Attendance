from __future__ import annotations

from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, IntPKMixin, TimestampMixin

if TYPE_CHECKING:
    from models.person import Person


class FaceEmbedding(IntPKMixin, TimestampMixin, Base):
    __tablename__ = "face_embeddings"

    person_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("persons.id", ondelete="CASCADE"))
    embedding = mapped_column(Vector(128), nullable=False)

    person: Mapped[Person] = relationship(back_populates="embeddings", lazy="raise")
