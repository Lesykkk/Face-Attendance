from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, IntPKMixin

if TYPE_CHECKING:
    from models.edge_node import EdgeNode
    from models.room import Room


class Building(IntPKMixin, Base):
    __tablename__ = "buildings"

    name: Mapped[str] = mapped_column(String(50), unique=True)

    rooms: Mapped[list[Room]] = relationship(back_populates="building", lazy="raise", passive_deletes=True)
    edge_nodes: Mapped[list[EdgeNode]] = relationship(back_populates="building", lazy="raise", passive_deletes=True)
