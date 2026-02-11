from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NewsPost(Base):
    __tablename__ = "news_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    cover_image_url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    created_at: Mapped[int] = mapped_column(nullable=False)
    updated_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_news_posts_salon_status_created", "salon_id", "status", "created_at"),
    )


class NewsEvent(Base):
    __tablename__ = "news_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    news_post_id: Mapped[int] = mapped_column(ForeignKey("news_posts.id", ondelete="CASCADE"), nullable=False)

    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    occurred_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_news_events_post_event_time", "news_post_id", "event_type", "occurred_at"),
        Index("ix_news_events_salon_time", "salon_id", "occurred_at"),
    )
