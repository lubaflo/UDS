from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CommunicationCampaign(Base):
    __tablename__ = "communication_campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False, default="marketing")  # marketing/reminder
    audience_type: Mapped[str] = mapped_column(String(32), nullable=False, default="consented_marketing")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft")  # draft/active/sent/archived
    schedule_type: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")  # manual/scheduled
    schedule_at: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_comm_campaigns_salon_status_created", "salon_id", "status", "created_at"),
    )


class CommunicationStep(Base):
    __tablename__ = "communication_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("communication_campaigns.id", ondelete="CASCADE"), nullable=False)
    step_order: Mapped[int] = mapped_column(nullable=False)
    channel: Mapped[str] = mapped_column(String(24), nullable=False)  # sms/app/email
    subject: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    body: Mapped[str] = mapped_column(String(4000), nullable=False)
    delay_minutes: Mapped[int] = mapped_column(nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("campaign_id", "step_order", name="uq_comm_steps_campaign_order"),
        Index("ix_comm_steps_campaign_order", "campaign_id", "step_order"),
    )


class CommunicationRecipient(Base):
    __tablename__ = "communication_recipients"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("communication_campaigns.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")  # pending/sent/opened/clicked/converted
    sent_at: Mapped[int | None] = mapped_column(nullable=True)
    opened_at: Mapped[int | None] = mapped_column(nullable=True)
    clicked_at: Mapped[int | None] = mapped_column(nullable=True)
    converted_at: Mapped[int | None] = mapped_column(nullable=True)
    delivery_channel: Mapped[str] = mapped_column(String(24), nullable=False, default="")

    __table_args__ = (
        UniqueConstraint("campaign_id", "client_id", name="uq_comm_recipients_campaign_client"),
        Index("ix_comm_recipients_campaign_status", "campaign_id", "status"),
        Index("ix_comm_recipients_client", "client_id"),
    )


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    service_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False, default="Процедура")
    starts_at: Mapped[int] = mapped_column(nullable=False)
    duration_minutes: Mapped[int] = mapped_column(nullable=False, default=60)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="scheduled")  # scheduled/cancelled/completed
    source: Mapped[str] = mapped_column(String(24), nullable=False, default="admin_manual")  # online/admin_phone/admin_manual

    __table_args__ = (
        Index("ix_appointments_salon_starts", "salon_id", "starts_at"),
        Index("ix_appointments_client_starts", "client_id", "starts_at"),
        Index("ix_appointments_salon_employee_starts", "salon_id", "employee_id", "starts_at"),
    )


class ReminderRule(Base):
    __tablename__ = "reminder_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)

    is_enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    offset_minutes: Mapped[int] = mapped_column(nullable=False)  # 60,240,1440,10080
    channel: Mapped[str] = mapped_column(String(24), nullable=False, default="app")

    __table_args__ = (
        UniqueConstraint("salon_id", "offset_minutes", "channel", name="uq_reminder_rule_unique"),
        Index("ix_reminder_rules_salon", "salon_id"),
    )


class ReminderDispatch(Base):
    __tablename__ = "reminder_dispatches"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("reminder_rules.id", ondelete="CASCADE"), nullable=False)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)

    scheduled_for: Mapped[int] = mapped_column(nullable=False)
    sent_at: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")  # pending/sent/skipped
    skip_reason: Mapped[str] = mapped_column(String(200), nullable=False, default="")

    __table_args__ = (
        UniqueConstraint("rule_id", "appointment_id", name="uq_reminder_once"),
        Index("ix_reminder_dispatch_rule_status", "rule_id", "status"),
        Index("ix_reminder_dispatch_sched", "scheduled_for", "status"),
    )
