from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import Client, Operation, TrafficChannel
from app.schemas.traffic import TrafficChannelCreateRequest, TrafficChannelListResponse, TrafficChannelOut
from app.services.security_service import write_audit

router = APIRouter(prefix="/admin/traffic-channels", tags=["admin.traffic"])


@router.get("", response_model=TrafficChannelListResponse)
def list_channels(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> TrafficChannelListResponse:
    q = (
        select(
            TrafficChannel,
            func.count(func.distinct(Client.id)).label("clients_count"),
            func.count(func.distinct(case((Operation.op_type == "purchase", Operation.client_id)))).label("buyers_count"),
            func.coalesce(func.sum(case((Operation.op_type == "purchase", Operation.amount_rub), else_=0)), 0).label("revenue_rub"),
        )
        .outerjoin(Client, and_(Client.acquisition_channel_id == TrafficChannel.id, Client.salon_id == ctx.salon_id))
        .outerjoin(Operation, and_(Operation.client_id == Client.id, Operation.salon_id == ctx.salon_id))
        .where(TrafficChannel.salon_id == ctx.salon_id)
        .group_by(TrafficChannel.id)
        .order_by(TrafficChannel.id.asc())
    )

    rows = db.execute(q).all()
    items = [
        TrafficChannelOut(
            id=row[0].id,
            name=row[0].name,
            channel_type=row[0].channel_type,
            promo_code=row[0].promo_code,
            clients_count=int(row[1] or 0),
            buyers_count=int(row[2] or 0),
            revenue_rub=int(row[3] or 0),
            created_at=row[0].created_at,
        )
        for row in rows
    ]
    return TrafficChannelListResponse(items=items)


@router.post("", response_model=TrafficChannelOut)
def create_channel(
    req: TrafficChannelCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> TrafficChannelOut:
    row = TrafficChannel(
        salon_id=ctx.salon_id,
        name=req.name,
        channel_type=req.channel_type,
        promo_code=req.promo_code,
        created_at=int(time.time()),
    )
    db.add(row)
    db.flush()
    write_audit(db, salon_id=ctx.salon_id, actor_user_id=ctx.user_id, action="traffic_channel.create", entity="traffic_channel", entity_id=str(row.id))
    return TrafficChannelOut(
        id=row.id,
        name=row.name,
        channel_type=row.channel_type,
        promo_code=row.promo_code,
        clients_count=0,
        buyers_count=0,
        revenue_rub=0,
        created_at=row.created_at,
    )
