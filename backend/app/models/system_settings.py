from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False, unique=True)

    weekly_report_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    global_search_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    responsible_first_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    responsible_last_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    responsible_phone: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    avg_purchases_per_day: Mapped[int] = mapped_column(nullable=False, default=0)

    __table_args__ = (
        Index("ix_system_settings_salon", "salon_id"),
    )
