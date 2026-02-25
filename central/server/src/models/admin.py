from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, IntPKMixin, TimestampMixin


class Admin(IntPKMixin, TimestampMixin, Base):
    __tablename__ = "admins"

    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
