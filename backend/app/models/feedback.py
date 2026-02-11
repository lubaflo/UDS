from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)

    feedback_type: Mapped[str] = mapped_column(String(24), nullable=False, default="rating")
    rating: Mapped[int | None] = mapped_column(nullable=True)
    text: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="new")
    created_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_feedback_salon_type_created", "salon_id", "feedback_type", "created_at"),
    )
