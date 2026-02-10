from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    tg_id: Mapped[int | None] = mapped_column(nullable=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")  # active/blacklist/etc
    notes: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    tags_csv: Mapped[str] = mapped_column(String(1000), nullable=False, default="")  # MVP: csv tags

    visits_count: Mapped[int] = mapped_column(nullable=False, default=0)
    total_spent_rub: Mapped[int] = mapped_column(nullable=False, default=0)  # MVP integer
    last_visit_at: Mapped[str] = mapped_column(String(32), nullable=False, default="")  # MVP iso string

    __table_args__ = (
        Index("ix_clients_salon_phone", "salon_id", "phone"),
        Index("ix_clients_salon_name", "salon_id", "name"),
    )