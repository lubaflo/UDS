from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tg_id", name="uq_users_tg_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)

    tg_id: Mapped[int] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="admin")  # owner/admin/operator/staff
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    display_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")

    salon = relationship("Salon")