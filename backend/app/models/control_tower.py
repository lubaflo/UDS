from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ControlTowerProfile(Base):
    __tablename__ = "control_tower_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False, unique=True)
    vertical: Mapped[str] = mapped_column(String(32), nullable=False, default="salon")
    goal_90d: Mapped[str] = mapped_column(String(255), nullable=False, default="Увеличить выручку на 15%")
    dashboard_focus: Mapped[str] = mapped_column(String(255), nullable=False, default="Выручка, конверсия и повторные покупки")
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (Index("ix_control_tower_profiles_salon", "salon_id"),)


class ProcessKPIConfig(Base):
    __tablename__ = "process_kpi_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    process_code: Mapped[str] = mapped_column(String(64), nullable=False)
    process_title: Mapped[str] = mapped_column(String(120), nullable=False)
    kpi_name: Mapped[str] = mapped_column(String(120), nullable=False)
    sla_name: Mapped[str] = mapped_column(String(120), nullable=False)
    sla_target: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    trigger_event: Mapped[str] = mapped_column(String(120), nullable=False)
    baseline_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    target_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    unit: Mapped[str] = mapped_column(String(16), nullable=False, default="percent")
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_orchestration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    __table_args__ = (
        Index("ix_process_kpi_configs_salon", "salon_id"),
        UniqueConstraint("salon_id", "process_code", name="uq_process_kpi_salon_code"),
    )


class ControlTowerPolicy(Base):
    __tablename__ = "control_tower_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False, unique=True)
    max_touches_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    min_hours_between_touches: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    channel_priority_csv: Mapped[str] = mapped_column(String(128), nullable=False, default="app_push,telegram,sms,email")
    min_phone_fill_percent: Mapped[float] = mapped_column(Float, nullable=False, default=80)
    min_consent_fill_percent: Mapped[float] = mapped_column(Float, nullable=False, default=90)
    enforce_quiet_hours: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    quiet_hours_start: Mapped[int] = mapped_column(Integer, nullable=False, default=22)
    quiet_hours_end: Mapped[int] = mapped_column(Integer, nullable=False, default=8)

    __table_args__ = (Index("ix_control_tower_policies_salon", "salon_id"),)


class OutcomeCatalogItem(Base):
    __tablename__ = "outcome_catalog_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    outcome_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    process_code: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    event_storming_steps: Mapped[str] = mapped_column(Text, nullable=False, default="")

    __table_args__ = (
        Index("ix_outcome_catalog_items_salon", "salon_id"),
        UniqueConstraint("salon_id", "outcome_code", name="uq_outcome_catalog_salon_code"),
    )
