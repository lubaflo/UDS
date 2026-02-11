from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="telegram")
    audience_type: Mapped[str] = mapped_column(String(32), nullable=False, default="all")
    message_text: Mapped[str] = mapped_column(String(4000), nullable=False)
    scheduled_at: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft")
    created_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_campaigns_salon_status_created", "salon_id", "status", "created_at"),
    )
