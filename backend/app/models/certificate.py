from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    amount_rub: Mapped[int] = mapped_column(nullable=False)
    issue_method: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="in_progress")
    expires_at: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_certificates_salon_status_created", "salon_id", "status", "created_at"),
    )
