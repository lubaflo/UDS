from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Salon(Base):
    __tablename__ = "salons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Moscow")
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="ru")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")