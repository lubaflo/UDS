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
    MessageOut,
    SendMessageRequest,
)
from app.services.messages_service import get_dialogue_history, list_dialogues, send_message

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
            channel=x.channel,
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
    )
    return MessageOut(
        id=row.id,
        direction=row.direction,
        channel=row.channel,
        text=row.text,
        subject=row.subject,
        destination=row.destination,
        created_at=row.created_at,
    )
