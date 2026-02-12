from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReferralProgramSetting(Base):
    __tablename__ = "referral_program_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False, unique=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reward_unit: Mapped[str] = mapped_column(String(16), nullable=False, default="points")
    max_generations: Mapped[int] = mapped_column(nullable=False, default=3)
    base_reward_value: Mapped[int] = mapped_column(nullable=False, default=100)

    __table_args__ = (
        Index("ix_referral_program_settings_salon", "salon_id"),
    )


class ReferralProgramGenerationRule(Base):
    __tablename__ = "referral_program_generation_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    setting_id: Mapped[int] = mapped_column(
        ForeignKey("referral_program_settings.id", ondelete="CASCADE"),
        nullable=False,
    )
    generation: Mapped[int] = mapped_column(nullable=False)
    reward_percent: Mapped[float] = mapped_column(nullable=False, default=0.0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_referral_rules_setting_generation", "setting_id", "generation", unique=True),
    )
