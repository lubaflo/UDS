from __future__ import annotations

import time

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models import (
    Appointment,
    Client,
    CommunicationCampaign,
    CommunicationRecipient,
    CommunicationStep,
    ReminderDispatch,
    ReminderRule,
)
from app.schemas.communications import CommunicationStepIn
from app.services.security_service import write_audit


def _can_receive_channel(client: Client, channel: str) -> bool:
    if channel == "sms":
        return bool(client.phone) and client.consent_marketing and client.consent_sms
    if channel == "app":
        return client.tg_id is not None and client.consent_marketing and client.consent_app_push
    if channel == "email":
        return bool(client.email) and client.consent_marketing and client.consent_email
    return False


def create_campaign(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int,
    title: str,
    purpose: str,
    audience_type: str,
    schedule_type: str,
    schedule_at: int | None,
    steps: list[CommunicationStepIn],
) -> CommunicationCampaign:
    campaign = CommunicationCampaign(
        salon_id=salon_id,
        title=title,
        purpose=purpose,
        audience_type=audience_type,
        status="active" if schedule_type == "scheduled" else "draft",
        schedule_type=schedule_type,
        schedule_at=schedule_at,
        created_at=int(time.time()),
    )
    db.add(campaign)
    db.flush()

    for step in sorted(steps, key=lambda x: x.step_order):
        db.add(
            CommunicationStep(
                campaign_id=campaign.id,
                step_order=step.step_order,
                channel=step.channel,
                subject=step.subject,
                body=step.body,
                delay_minutes=step.delay_minutes,
            )
        )
    db.flush()

    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action="communication_campaign.create",
        entity="communication_campaign",
        entity_id=str(campaign.id),
    )
    return campaign


def list_campaigns(db: Session, *, salon_id: int, status: str | None) -> tuple[list[CommunicationCampaign], int, int]:
    q = select(CommunicationCampaign).where(CommunicationCampaign.salon_id == salon_id)
    if status == "active":
        q = q.where(CommunicationCampaign.status.in_(["draft", "active", "sent"]))
    elif status == "archive":
        q = q.where(CommunicationCampaign.status == "archived")

    items = db.execute(q.order_by(CommunicationCampaign.id.desc())).scalars().all()
    active_count = int(
        db.execute(
            select(func.count()).where(
                and_(
                    CommunicationCampaign.salon_id == salon_id,
                    CommunicationCampaign.status.in_(["draft", "active", "sent"]),
                )
            )
        ).scalar_one()
        or 0
    )
    archived_count = int(
        db.execute(
            select(func.count()).where(
                and_(CommunicationCampaign.salon_id == salon_id, CommunicationCampaign.status == "archived")
            )
        ).scalar_one()
        or 0
    )
    return items, active_count, archived_count


def get_campaign_steps(db: Session, campaign_id: int) -> list[CommunicationStep]:
    return db.execute(
        select(CommunicationStep)
        .where(CommunicationStep.campaign_id == campaign_id)
        .order_by(CommunicationStep.step_order.asc())
    ).scalars().all()


def _selected_clients(db: Session, salon_id: int, audience_type: str) -> list[Client]:
    q = select(Client).where(Client.salon_id == salon_id, Client.consent_personal_data == True)
    if audience_type == "consented_marketing":
        q = q.where(Client.consent_marketing == True)
    return db.execute(q).scalars().all()


def launch_campaign(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int,
    campaign_id: int,
) -> tuple[int, int]:
    campaign = db.execute(
        select(CommunicationCampaign).where(
            CommunicationCampaign.id == campaign_id,
            CommunicationCampaign.salon_id == salon_id,
        )
    ).scalar_one()
    steps = get_campaign_steps(db, campaign_id)
    if not steps:
        return 0, 0

    clients = _selected_clients(db, salon_id, campaign.audience_type)
    queued = 0
    first_channel = steps[0].channel

    for client in clients:
        if not _can_receive_channel(client, first_channel):
            continue
        exists = db.execute(
            select(CommunicationRecipient).where(
                CommunicationRecipient.campaign_id == campaign_id,
                CommunicationRecipient.client_id == client.id,
            )
        ).scalar_one_or_none()
        if exists:
            continue

        db.add(
            CommunicationRecipient(
                campaign_id=campaign_id,
                client_id=client.id,
                status="sent",
                sent_at=int(time.time()),
                delivery_channel=first_channel,
            )
        )
        queued += 1

    campaign.status = "sent"
    db.flush()
    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action="communication_campaign.launch",
        entity="communication_campaign",
        entity_id=str(campaign_id),
        meta_json=f"queued={queued}",
    )
    return len(clients), queued


def track_recipient_event(db: Session, recipient_id: int, event: str) -> CommunicationRecipient:
    row = db.execute(select(CommunicationRecipient).where(CommunicationRecipient.id == recipient_id)).scalar_one()
    now = int(time.time())
    if event == "open":
        row.opened_at = now
        if row.status in {"pending", "sent"}:
            row.status = "opened"
    elif event == "click":
        row.clicked_at = now
        row.status = "clicked"
    elif event == "conversion":
        row.converted_at = now
        row.status = "converted"
    return row


def campaign_stats(db: Session, campaign_id: int) -> tuple[int, int, int, int, int]:
    rows = db.execute(
        select(CommunicationRecipient).where(CommunicationRecipient.campaign_id == campaign_id)
    ).scalars().all()
    total = len(rows)
    sent = len([x for x in rows if x.sent_at is not None])
    opened = len([x for x in rows if x.opened_at is not None])
    clicked = len([x for x in rows if x.clicked_at is not None])
    converted = len([x for x in rows if x.converted_at is not None])
    return total, sent, opened, clicked, converted


def set_reminder_rules(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int,
    rules: list[tuple[int, str, bool]],
) -> list[ReminderRule]:
    db.query(ReminderRule).filter(ReminderRule.salon_id == salon_id).delete()
    for offset_minutes, channel, enabled in rules:
        db.add(
            ReminderRule(
                salon_id=salon_id,
                offset_minutes=offset_minutes,
                channel=channel,
                is_enabled=enabled,
            )
        )
    db.flush()
    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action="reminder_rules.update",
        entity="reminder_rule",
    )
    return db.execute(select(ReminderRule).where(ReminderRule.salon_id == salon_id)).scalars().all()


def get_reminder_rules(db: Session, salon_id: int) -> list[ReminderRule]:
    return db.execute(
        select(ReminderRule).where(ReminderRule.salon_id == salon_id).order_by(ReminderRule.offset_minutes.asc())
    ).scalars().all()


def create_appointment(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int,
    client_id: int,
    title: str,
    starts_at: int,
) -> Appointment:
    row = Appointment(
        salon_id=salon_id,
        client_id=client_id,
        title=title,
        starts_at=starts_at,
        status="scheduled",
    )
    db.add(row)
    db.flush()

    rules = get_reminder_rules(db, salon_id)
    for rule in rules:
        scheduled_for = starts_at - rule.offset_minutes * 60
        db.add(
            ReminderDispatch(
                rule_id=rule.id,
                appointment_id=row.id,
                client_id=client_id,
                scheduled_for=scheduled_for,
                status="pending",
            )
        )

    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action="appointment.create",
        entity="appointment",
        entity_id=str(row.id),
    )
    return row


def run_reminders(db: Session, salon_id: int, now_ts: int | None = None) -> tuple[int, int, int]:
    now = now_ts or int(time.time())
    rows = db.execute(
        select(ReminderDispatch, ReminderRule, Client)
        .join(ReminderRule, ReminderRule.id == ReminderDispatch.rule_id)
        .join(Client, Client.id == ReminderDispatch.client_id)
        .where(
            ReminderRule.salon_id == salon_id,
            ReminderDispatch.status == "pending",
            ReminderDispatch.scheduled_for <= now,
        )
    ).all()

    processed = len(rows)
    sent = 0
    skipped = 0
    for dispatch, rule, client in rows:
        if not rule.is_enabled:
            dispatch.status = "skipped"
            dispatch.skip_reason = "rule_disabled"
            skipped += 1
            continue
        if not client.consent_personal_data:
            dispatch.status = "skipped"
            dispatch.skip_reason = "no_personal_data_consent"
            skipped += 1
            continue

        channel_ok = True
        if rule.channel == "sms":
            channel_ok = bool(client.phone) and client.consent_sms
        elif rule.channel == "app":
            channel_ok = client.tg_id is not None and client.consent_app_push
        elif rule.channel == "email":
            channel_ok = bool(client.email) and client.consent_email

        if not channel_ok:
            dispatch.status = "skipped"
            dispatch.skip_reason = "channel_consent_or_contacts_missing"
            skipped += 1
            continue

        dispatch.status = "sent"
        dispatch.sent_at = now
        sent += 1

    return processed, sent, skipped


def get_campaign_by_id(db: Session, *, salon_id: int, campaign_id: int) -> CommunicationCampaign:
    return db.execute(
        select(CommunicationCampaign).where(
            CommunicationCampaign.id == campaign_id,
            CommunicationCampaign.salon_id == salon_id,
        )
    ).scalar_one()


def create_workflow_campaign(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int,
    title: str,
) -> CommunicationCampaign:
    row = CommunicationCampaign(
        salon_id=salon_id,
        title=title,
        purpose="marketing",
        audience_type="consented_marketing",
        status="draft",
        schedule_type="manual",
        schedule_at=None,
        created_at=int(time.time()),
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action="communication_workflow.create",
        entity="communication_campaign",
        entity_id=str(row.id),
    )
    return row


def workflow_step1_audience(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int,
    campaign_id: int,
    purpose: str,
    audience_type: str,
) -> CommunicationCampaign:
    row = get_campaign_by_id(db, salon_id=salon_id, campaign_id=campaign_id)
    row.purpose = purpose
    row.audience_type = audience_type
    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action="communication_workflow.step1",
        entity="communication_campaign",
        entity_id=str(campaign_id),
        meta_json=f"purpose={purpose};audience={audience_type}",
    )
    return row


def workflow_step2_content(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int,
    campaign_id: int,
    steps: list[CommunicationStepIn],
) -> list[CommunicationStep]:
    _ = get_campaign_by_id(db, salon_id=salon_id, campaign_id=campaign_id)
    db.query(CommunicationStep).filter(CommunicationStep.campaign_id == campaign_id).delete()
    for step in sorted(steps, key=lambda x: x.step_order):
        db.add(
            CommunicationStep(
                campaign_id=campaign_id,
                step_order=step.step_order,
                channel=step.channel,
                subject=step.subject,
                body=step.body,
                delay_minutes=step.delay_minutes,
            )
        )
    db.flush()
    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action="communication_workflow.step2",
        entity="communication_campaign",
        entity_id=str(campaign_id),
        meta_json=f"steps={len(steps)}",
    )
    return get_campaign_steps(db, campaign_id)


def workflow_step3_schedule(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int,
    campaign_id: int,
    schedule_type: str,
    schedule_at: int | None,
) -> CommunicationCampaign:
    row = get_campaign_by_id(db, salon_id=salon_id, campaign_id=campaign_id)
    row.schedule_type = schedule_type
    row.schedule_at = schedule_at
    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action="communication_workflow.step3",
        entity="communication_campaign",
        entity_id=str(campaign_id),
    )
    return row


def workflow_estimated_recipients(db: Session, *, salon_id: int, campaign_id: int) -> int:
    campaign = get_campaign_by_id(db, salon_id=salon_id, campaign_id=campaign_id)
    steps = get_campaign_steps(db, campaign_id)
    if not steps:
        return 0
    first_channel = steps[0].channel
    clients = _selected_clients(db, salon_id, campaign.audience_type)
    return len([x for x in clients if _can_receive_channel(x, first_channel)])


def workflow_state(db: Session, *, salon_id: int, campaign_id: int) -> tuple[int, bool, bool, bool, bool]:
    campaign = get_campaign_by_id(db, salon_id=salon_id, campaign_id=campaign_id)
    has_audience = bool(campaign.purpose and campaign.audience_type)
    has_content = len(get_campaign_steps(db, campaign_id)) > 0
    has_schedule = campaign.schedule_type in {"manual", "scheduled"}
    can_confirm = has_audience and has_content and has_schedule

    current_step = 1
    if has_audience:
        current_step = 2
    if has_content:
        current_step = 3
    if has_schedule:
        current_step = 4
    if campaign.status in {"sent", "archived"}:
        current_step = 5

    return current_step, can_confirm, has_audience, has_content, has_schedule
