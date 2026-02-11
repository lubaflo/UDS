from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import Client
from app.schemas.messages import (
    DialogueHistoryResponse,
    DialogueItem,
    DialogueListResponse,
    GroupSendMessageRequest,
    GroupSendMessageResponse,
    MessageOut,
    MessageRegistryItem,
    MessageRegistryResponse,
    SendMessageRequest,
)
from app.services.messages_service import (
    get_dialogue_history,
    list_dialogues,
    list_messages_registry,
    send_group_message,
    send_message,
)

router = APIRouter(prefix="/admin/dialogues", tags=["admin.messages"])


@router.get("", response_model=DialogueListResponse)
def get_dialogues(
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    ctx=Depends(require_roles("owner", "admin", "operator")),
    db: Session = Depends(get_db),
) -> DialogueListResponse:
    rows, total = list_dialogues(db, salon_id=ctx.salon_id, query=q, page=page, page_size=page_size)
    items = [
        DialogueItem(
            client_id=r[0],
            client_tg_id=r[1],
            client_name=r[2] or "",
            client_phone=r[3] or "",
            last_message_at=int(r[4] or 0),
            last_message_text=r[5] or "",
            last_message_channel=r[6] or "telegram",
        )
        for r in rows
    ]
    return DialogueListResponse(items=items, page=page, page_size=page_size, total=total)


@router.get("/messages", response_model=MessageRegistryResponse)
def get_messages_registry(
    message_date: int | None = Query(default=None, ge=0, description="Unix time начала суток для фильтра по дате"),
    date_from: int | None = Query(default=None, ge=0),
    date_to: int | None = Query(default=None, ge=0),
    fio: str | None = Query(default=None),
    delivery_status: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    ctx=Depends(require_roles("owner", "admin", "operator")),
    db: Session = Depends(get_db),
) -> MessageRegistryResponse:
    rows, total = list_messages_registry(
        db,
        salon_id=ctx.salon_id,
        message_date=message_date,
        date_from=date_from,
        date_to=date_to,
        fio=fio,
        delivery_status=delivery_status,
        channel=channel,
        page=page,
        page_size=page_size,
    )
    items = [
        MessageRegistryItem(
            message_id=r[0],
            client_id=r[1],
            client_name=r[2] or "",
            channel=r[3],
            delivery_status=r[4],
            message_type=r[5],
            group_name=r[6] or "",
            text=r[7],
            created_at=r[8],
            scheduled_for=r[9],
        )
        for r in rows
    ]
    return MessageRegistryResponse(items=items, page=page, page_size=page_size, total=total)


@router.get("/{client_id}", response_model=DialogueHistoryResponse)
def get_dialogue(
    client_id: int,
    ctx=Depends(require_roles("owner", "admin", "operator")),
    db: Session = Depends(get_db),
) -> DialogueHistoryResponse:
    client = db.execute(select(Client).where(Client.salon_id == ctx.salon_id, Client.id == client_id)).scalar_one()
    rows = get_dialogue_history(db, salon_id=ctx.salon_id, client_id=client_id)
    items = [
        MessageOut(
            id=x.id,
            direction=x.direction,
            message_type=x.message_type,
            group_name=x.group_name,
            channel=x.channel,
            delivery_status=x.delivery_status,
            scheduled_for=x.scheduled_for,
            text=x.text,
            subject=x.subject,
            destination=x.destination,
            created_at=x.created_at,
        )
        for x in rows
    ]
    return DialogueHistoryResponse(client_id=client_id, client_tg_id=client.tg_id, items=items)


@router.post("/{client_id}/send", response_model=MessageOut)
def post_send(
    client_id: int,
    req: SendMessageRequest,
    ctx=Depends(require_roles("owner", "admin", "operator")),
    db: Session = Depends(get_db),
) -> MessageOut:
    row = send_message(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        client_id=client_id,
        channel=req.channel,
        subject=req.subject,
        text=req.text,
        delivery_status=req.delivery_status,
        scheduled_for=req.scheduled_for,
    )
    return MessageOut(
        id=row.id,
        direction=row.direction,
        message_type=row.message_type,
        group_name=row.group_name,
        channel=row.channel,
        delivery_status=row.delivery_status,
        scheduled_for=row.scheduled_for,
        text=row.text,
        subject=row.subject,
        destination=row.destination,
        created_at=row.created_at,
    )


@router.post("/send-group", response_model=GroupSendMessageResponse)
def post_send_group(
    req: GroupSendMessageRequest,
    ctx=Depends(require_roles("owner", "admin", "operator")),
    db: Session = Depends(get_db),
) -> GroupSendMessageResponse:
    rows = send_group_message(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        client_ids=req.client_ids,
        group_name=req.group_name,
        channel=req.channel,
        subject=req.subject,
        text=req.text,
        delivery_status=req.delivery_status,
        scheduled_for=req.scheduled_for,
    )
    items = [
        MessageOut(
            id=x.id,
            direction=x.direction,
            message_type=x.message_type,
            group_name=x.group_name,
            channel=x.channel,
            delivery_status=x.delivery_status,
            scheduled_for=x.scheduled_for,
            text=x.text,
            subject=x.subject,
            destination=x.destination,
            created_at=x.created_at,
        )
        for x in rows
    ]
    return GroupSendMessageResponse(group_name=req.group_name, sent_count=len(items), items=items)
