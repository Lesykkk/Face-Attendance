from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, IntPKMixin

if TYPE_CHECKING:
    from models.building import Building
    from models.camera import Camera


class EdgeNode(IntPKMixin, Base):
    __tablename__ = "edge_nodes"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    api_key_hash: Mapped[str] = mapped_column(String(255))
    building_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("buildings.id", ondelete="RESTRICT"))

    building: Mapped[Building] = relationship(back_populates="edge_nodes",lazy="raise")
    cameras: Mapped[list[Camera]] = relationship(back_populates="edge_node", lazy="raise", passive_deletes=True)
