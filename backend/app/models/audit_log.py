from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)

    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    meta_json: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    created_at: Mapped[int] = mapped_column(nullable=False)  # unix ts

    __table_args__ = (
        Index("ix_audit_salon_created", "salon_id", "created_at"),
        Index("ix_audit_salon_actor_created", "salon_id", "actor_user_id", "created_at"),
    )