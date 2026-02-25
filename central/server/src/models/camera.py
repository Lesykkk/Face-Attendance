from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, IntPKMixin

if TYPE_CHECKING:
    from models.room import Room
    from models.edge_node import EdgeNode


class Camera(IntPKMixin, Base):
    __tablename__ = "cameras"

    room_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rooms.id", ondelete="CASCADE"))
    edge_node_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("edge_nodes.id", ondelete="CASCADE"))
    rtsp_url: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    room: Mapped[Room] = relationship(back_populates="cameras", lazy="raise")
    edge_node: Mapped[EdgeNode] = relationship(back_populates="cameras", lazy="raise")