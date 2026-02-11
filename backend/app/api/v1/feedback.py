from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import SecurityError, verify_telegram_init_data
from app.models import Feedback, Message, Salon
from app.schemas.app_feedback import (
    AppFeedbackCreateRequest,
    AppFeedbackCreateResponse,
    AppMessageCreateRequest,
    AppMessageCreateResponse,
)
from app.services.clients_service import get_or_create_client_by_tg_id

router = APIRouter(prefix="/feedback/app", tags=["app.feedback"])


def _resolve_salon_id(db: Session) -> int:
    salon = db.execute(select(Salon).limit(1)).scalar_one_or_none()
    if salon is None:
        raise HTTPException(status_code=400, detail="Salon not initialized")
    return salon.id


@router.post("/rating", response_model=AppFeedbackCreateResponse)
def create_rating(req: AppFeedbackCreateRequest, db: Session = Depends(get_db)) -> AppFeedbackCreateResponse:
    try:
        tg_user = verify_telegram_init_data(req.init_data)
    except SecurityError as e:
        raise HTTPException(status_code=401, detail=str(e))

    salon_id = _resolve_salon_id(db)
    client = get_or_create_client_by_tg_id(
        db,
        salon_id=salon_id,
        tg_id=tg_user.tg_id,
        username=tg_user.username or "",
        full_name=f"{tg_user.first_name or ''} {tg_user.last_name or ''}".strip(),
    )

    row = Feedback(
        salon_id=salon_id,
        client_id=client.id,
        feedback_type=req.feedback_type,
        object_type=req.object_type,
        object_id=req.object_id,
        rating=req.rating,
        text=req.text,
        status="new",
        created_at=int(time.time()),
    )
    db.add(row)
    db.flush()

    return AppFeedbackCreateResponse(client_id=client.id, feedback_id=row.id)


@router.post("/message", response_model=AppMessageCreateResponse)
def create_message(req: AppMessageCreateRequest, db: Session = Depends(get_db)) -> AppMessageCreateResponse:
    try:
        tg_user = verify_telegram_init_data(req.init_data)
    except SecurityError as e:
        raise HTTPException(status_code=401, detail=str(e))

    salon_id = _resolve_salon_id(db)
    client = get_or_create_client_by_tg_id(
        db,
        salon_id=salon_id,
        tg_id=tg_user.tg_id,
        username=tg_user.username or "",
        full_name=f"{tg_user.first_name or ''} {tg_user.last_name or ''}".strip(),
    )

    row = Message(
        salon_id=salon_id,
        client_id=client.id,
        client_tg_id=client.tg_id,
        direction="in",
        channel=req.channel,
        subject="",
        destination=str(client.tg_id or ""),
        text=req.text,
        created_at=int(time.time()),
    )
    db.add(row)
    db.flush()

    return AppMessageCreateResponse(client_id=client.id, message_id=row.id)
