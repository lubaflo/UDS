from __future__ import annotations

import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Client, Message
from app.services.security_service import write_audit


def list_dialogues(
    db: Session,
    *,
    salon_id: int,
    query: str | None,
    page: int,
    page_size: int,
) -> tuple[list[tuple[int, int | None, str, str, int, str, str]], int]:
    # Dialogue = last message per client
    base = (
        select(
            Message.client_id.label("client_id"),
            func.max(Message.created_at).label("last_ts"),
        )
        .where(Message.salon_id == salon_id)
        .group_by(Message.client_id)
        .subquery()
    )

    q = (
        select(
            Client.id,
            Client.tg_id,
            Client.full_name,
            Client.phone,
            base.c.last_ts,
            Message.text,
            Message.channel,
        )
        .join(base, base.c.client_id == Client.id)
        .join(Message, (Message.client_id == Client.id) & (Message.created_at == base.c.last_ts))
        .where(Client.salon_id == salon_id)
        .order_by(base.c.last_ts.desc())
    )

    if query:
        like = f"%{query.strip()}%"
        q = q.where((Client.full_name.ilike(like)) | (Client.phone.ilike(like)) | (Message.text.ilike(like)))

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    rows = db.execute(q.offset((page - 1) * page_size).limit(page_size)).all()
    return rows, int(total)


def get_dialogue_history(db: Session, *, salon_id: int, client_id: int) -> list[Message]:
    q = (
        select(Message)
        .where(Message.salon_id == salon_id, Message.client_id == client_id)
        .order_by(Message.created_at.asc())
    )
    return db.execute(q).scalars().all()


def list_messages_registry(
    db: Session,
    *,
    salon_id: int,
    date_from: int | None,
    date_to: int | None,
    message_date: int | None,
    fio: str | None,
    delivery_status: str | None,
    channel: str | None,
    page: int,
    page_size: int,
) -> tuple[list[tuple[int, int, str, str, str, str, str, str, int, int | None]], int]:
    q = (
        select(
            Message.id,
            Message.client_id,
            Client.full_name,
            Message.channel,
            Message.delivery_status,
            Message.message_type,
            Message.group_name,
            Message.text,
            Message.created_at,
            Message.scheduled_for,
        )
        .join(Client, Client.id == Message.client_id)
        .where(Message.salon_id == salon_id, Client.salon_id == salon_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
    )

    if message_date is not None:
        day_start = message_date
        day_end = message_date + 86400
        q = q.where(Message.created_at >= day_start, Message.created_at < day_end)
    if date_from is not None:
        q = q.where(Message.created_at >= date_from)
    if date_to is not None:
        q = q.where(Message.created_at <= date_to)
    if fio:
        like = f"%{fio.strip()}%"
        q = q.where(Client.full_name.ilike(like))
    if delivery_status:
        q = q.where(Message.delivery_status == delivery_status)
    if channel:
        q = q.where(Message.channel == channel)

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    rows = db.execute(q.offset((page - 1) * page_size).limit(page_size)).all()
    return rows, int(total)


def _pick_destination(client: Client, channel: str) -> str:
    if channel == "telegram":
        return str(client.tg_id or "")
    if channel == "sms":
        return client.phone
    if channel == "email":
        return client.email
    if channel == "vk":
        return client.vk_username
    if channel == "instagram":
        return client.instagram_username
    if channel == "facebook":
        return client.facebook_username
    if channel == "max":
        return client.max_username
    return ""


def send_message(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int | None,
    client_id: int,
    channel: str,
    subject: str,
    text: str,
    delivery_status: str = "sent",
    scheduled_for: int | None = None,
    message_type: str = "individual",
    group_name: str = "",
) -> Message:
    client = db.execute(select(Client).where(Client.salon_id == salon_id, Client.id == client_id)).scalar_one()
    destination = _pick_destination(client, channel)

    row = Message(
        salon_id=salon_id,
        client_id=client_id,
        client_tg_id=client.tg_id,
        direction="out",
        message_type=message_type,
        group_name=group_name,
        channel=channel,
        delivery_status=delivery_status,
        scheduled_for=scheduled_for,
        subject=subject,
        destination=destination,
        text=text,
        created_at=int(time.time()),
    )
    db.add(row)
    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action="message.send",
        entity="client",
        entity_id=str(client_id),
        meta_json=f"{channel};{message_type};{delivery_status}",
    )
    return row


def send_group_message(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int | None,
    client_ids: list[int],
    group_name: str,
    channel: str,
    subject: str,
    text: str,
    delivery_status: str,
    scheduled_for: int | None,
) -> list[Message]:
    messages: list[Message] = []
    for client_id in client_ids:
        row = send_message(
            db,
            salon_id=salon_id,
            actor_user_id=actor_user_id,
            client_id=client_id,
            channel=channel,
            subject=subject,
            text=text,
            delivery_status=delivery_status,
            scheduled_for=scheduled_for,
            message_type="group",
            group_name=group_name,
        )
        messages.append(row)

    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action="message.group_send",
        entity="message_group",
        entity_id=group_name,
        meta_json=f"count={len(messages)};channel={channel};delivery_status={delivery_status}",
    )
    return messages
