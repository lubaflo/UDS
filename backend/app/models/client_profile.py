from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ClientChild(Base):
    __tablename__ = "client_children"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)

    full_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    birth_date: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    notes: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    __table_args__ = (
        Index("ix_client_children_salon_client", "salon_id", "client_id"),
    )


class ClientLoyaltyProgram(Base):
    __tablename__ = "client_loyalty_programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)

    program_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    level_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    balance: Mapped[int] = mapped_column(nullable=False, default=0)
    expires_at: Mapped[int | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index("ix_client_loyalty_programs_salon_client", "salon_id", "client_id"),
    )


class ClientGroupRule(Base):
    __tablename__ = "client_group_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)

    group_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    min_visits: Mapped[int] = mapped_column(nullable=False, default=0)
    min_total_spent_rub: Mapped[int] = mapped_column(nullable=False, default=0)
    inactive_days_over: Mapped[int] = mapped_column(nullable=False, default=0)
    require_marketing_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_client_group_rules_salon", "salon_id"),
    )
