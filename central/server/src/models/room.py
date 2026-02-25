from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, IntPKMixin

if TYPE_CHECKING:
    from models.building import Building
    from models.camera import Camera


class Room(IntPKMixin, Base):
    __tablename__ = "rooms"
    __table_args__ = (
        UniqueConstraint("building_id", "name", name="uq_room_building_name"),
    )

    building_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("buildings.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(50))

    building: Mapped[Building] = relationship(back_populates="rooms", lazy="raise")
    cameras: Mapped[list[Camera]] = relationship(back_populates="room", lazy="raise", passive_deletes=True)
