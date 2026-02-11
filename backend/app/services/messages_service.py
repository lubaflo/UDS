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
) -> tuple[list[tuple[int, str, str, int, str]], int]:
    # Dialogue = last message per client
    # MVP query: messages grouped by client_id
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
            Client.full_name,
            Client.phone,
            base.c.last_ts,
            Message.text,
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
    # rows: (client_id, name, phone, last_ts, text)
    return rows, int(total)


def get_dialogue_history(db: Session, *, salon_id: int, client_id: int) -> list[Message]:
    q = (
        select(Message)
        .where(Message.salon_id == salon_id, Message.client_id == client_id)
        .order_by(Message.created_at.asc())
    )
    return db.execute(q).scalars().all()


def send_message(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int | None,
    client_id: int,
    text: str,
) -> Message:
    row = Message(
        salon_id=salon_id,
        client_id=client_id,
        direction="out",
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
        meta_json="",
    )
    return row