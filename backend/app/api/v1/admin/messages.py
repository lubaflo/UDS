from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
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
            client_name=r[1] or "",
            client_phone=r[2] or "",
            last_message_at=int(r[3] or 0),
            last_message_text=r[4] or "",
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
    rows = get_dialogue_history(db, salon_id=ctx.salon_id, client_id=client_id)
    items = [MessageOut(id=x.id, direction=x.direction, text=x.text, created_at=x.created_at) for x in rows]
    return DialogueHistoryResponse(client_id=client_id, items=items)


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
        text=req.text,
    )
    return MessageOut(id=row.id, direction=row.direction, text=row.text, created_at=row.created_at)