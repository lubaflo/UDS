from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import Client, Operation
from app.schemas.operations import OperationCreateRequest, OperationListResponse, OperationOut
from app.services.security_service import write_audit

router = APIRouter(prefix="/admin/operations", tags=["admin.operations"])


@router.get("", response_model=OperationListResponse)
def list_ops(
    date_from: int | None = Query(default=None),
    date_to: int | None = Query(default=None),
    op_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> OperationListResponse:
    q = select(Operation).where(Operation.salon_id == ctx.salon_id)
    if date_from is not None:
        q = q.where(Operation.created_at >= date_from)
    if date_to is not None:
        q = q.where(Operation.created_at <= date_to)
    if op_type:
        q = q.where(Operation.op_type == op_type)
    q = q.order_by(Operation.created_at.desc())

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    items = db.execute(q.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return OperationListResponse(
        items=[OperationOut.model_validate(x, from_attributes=True) for x in items],
        page=page,
        page_size=page_size,
        total=int(total),
    )


@router.post("", response_model=OperationOut)
def create_op(
    req: OperationCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> OperationOut:
    client = db.execute(
        select(Client).where(and_(Client.id == req.client_id, Client.salon_id == ctx.salon_id))
    ).scalar_one()

    row = Operation(
        salon_id=ctx.salon_id,
        client_id=req.client_id,
        op_type=req.op_type,
        amount_rub=req.amount_rub,
        discount_rub=req.discount_rub,
        referral_discount_rub=req.referral_discount_rub,
        comment=req.comment,
        created_at=int(time.time()),
    )
    db.add(row)

    if req.op_type in {"purchase", "order"}:
        client.visits_count += 1
        client.total_spent_rub += max(req.amount_rub - req.discount_rub - req.referral_discount_rub, 0)
        client.last_visit_at = row.created_at

    write_audit(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        action="operation.create",
        entity="operation",
        entity_id=str(row.id),
    )
    db.flush()
    return OperationOut.model_validate(row, from_attributes=True)
