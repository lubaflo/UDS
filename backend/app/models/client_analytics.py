from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ClientAnalytics(Base):
    __tablename__ = "client_analytics"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    created_at: Mapped[int] = mapped_column(nullable=False)
    gender: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown")
    birth_year: Mapped[int | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index("ix_client_analytics_salon_created", "salon_id", "created_at"),
        Index("ix_client_analytics_salon_gender", "salon_id", "gender"),
    )
