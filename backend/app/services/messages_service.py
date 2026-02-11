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
) -> Message:
    client = db.execute(select(Client).where(Client.salon_id == salon_id, Client.id == client_id)).scalar_one()
    destination = _pick_destination(client, channel)

    row = Message(
        salon_id=salon_id,
        client_id=client_id,
        client_tg_id=client.tg_id,
        direction="out",
        channel=channel,
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
        meta_json=channel,
    )
    return row
