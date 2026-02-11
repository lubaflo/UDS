from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import Feedback
from app.schemas.feedback import FeedbackCreateRequest, FeedbackListResponse, FeedbackOut
from app.services.security_service import write_audit

router = APIRouter(prefix="/admin/feedback", tags=["admin.feedback"])


@router.get("", response_model=FeedbackListResponse)
def list_feedback(
    feedback_type: str | None = Query(default=None),
    object_type: str | None = Query(default=None),
    object_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> FeedbackListResponse:
    q = select(Feedback).where(Feedback.salon_id == ctx.salon_id)
    if feedback_type:
        q = q.where(Feedback.feedback_type == feedback_type)
    if object_type:
        q = q.where(Feedback.object_type == object_type)
    if object_id is not None:
        q = q.where(Feedback.object_id == object_id)

    q = q.order_by(Feedback.created_at.desc())
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    rows = db.execute(q.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return FeedbackListResponse(
        items=[FeedbackOut.model_validate(x, from_attributes=True) for x in rows],
        page=page,
        page_size=page_size,
        total=int(total),
    )


@router.post("", response_model=FeedbackOut)
def create_feedback(
    req: FeedbackCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> FeedbackOut:
    row = Feedback(
        salon_id=ctx.salon_id,
        client_id=req.client_id,
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
    write_audit(db, salon_id=ctx.salon_id, actor_user_id=ctx.user_id, action="feedback.create", entity="feedback", entity_id=str(row.id))
    return FeedbackOut.model_validate(row, from_attributes=True)
