from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)

    direction: Mapped[str] = mapped_column(String(16), nullable=False)  # in/out
    text: Mapped[str] = mapped_column(String(4000), nullable=False, default="")
    created_at: Mapped[int] = mapped_column(nullable=False)  # unix ts

    __table_args__ = (
        Index("ix_messages_salon_client_created", "salon_id", "client_id", "created_at"),
    )