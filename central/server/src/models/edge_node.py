from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, IntPKMixin

if TYPE_CHECKING:
    from models.camera import Camera


class EdgeNode(IntPKMixin, Base):
    __tablename__ = "edge_nodes"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    api_key_hash: Mapped[str] = mapped_column(String(255))

    cameras: Mapped[list[Camera]] = relationship(back_populates="edge_node", lazy="raise", passive_deletes=True)
