from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)

    tg_id: Mapped[int | None] = mapped_column(nullable=True)
    username: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    whatsapp_phone: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(254), nullable=False, default="")
    telegram_username: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    vk_username: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    instagram_username: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    facebook_username: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    max_username: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    address: Mapped[str] = mapped_column(String(400), nullable=False, default="")
    birthday: Mapped[str] = mapped_column(String(10), nullable=False, default="")

    consent_personal_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_marketing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_sms: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_app_push: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    notes: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    tags_csv: Mapped[str] = mapped_column(String(1000), nullable=False, default="")

    acquisition_channel_id: Mapped[int | None] = mapped_column(
        ForeignKey("traffic_channels.id", ondelete="SET NULL"), nullable=True
    )

    visits_count: Mapped[int] = mapped_column(nullable=False, default=0)
    total_spent_rub: Mapped[int] = mapped_column(nullable=False, default=0)
    last_visit_at: Mapped[int | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index("ix_clients_salon_phone", "salon_id", "phone"),
        Index("ix_clients_salon_email", "salon_id", "email"),
        Index("ix_clients_salon_full_name", "salon_id", "full_name"),
        Index("ix_clients_salon_tg", "salon_id", "tg_id"),
    )
