from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    client_tg_id: Mapped[int | None] = mapped_column(nullable=True)

    direction: Mapped[str] = mapped_column(String(16), nullable=False)  # in/out
    channel: Mapped[str] = mapped_column(String(24), nullable=False, default="telegram")
    subject: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    destination: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    text: Mapped[str] = mapped_column(String(4000), nullable=False, default="")
    created_at: Mapped[int] = mapped_column(nullable=False)  # unix ts

    __table_args__ = (
        Index("ix_messages_salon_client_created", "salon_id", "client_id", "created_at"),
        Index("ix_messages_salon_tg_created", "salon_id", "client_tg_id", "created_at"),
    )
