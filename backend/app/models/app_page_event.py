from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AppPageEvent(Base):
    __tablename__ = "app_page_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)

    event_type: Mapped[str] = mapped_column(String(16), nullable=False, default="view")  # view/visitor
    visitor_key: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    page_code: Mapped[str] = mapped_column(String(64), nullable=False, default="company")
    created_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_app_events_salon_created", "salon_id", "created_at"),
        Index("ix_app_events_salon_visitor_created", "salon_id", "visitor_key", "created_at"),
    )
