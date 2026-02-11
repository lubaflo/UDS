from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import Campaign
from app.schemas.campaigns import (
    CampaignCreateRequest,
    CampaignListResponse,
    CampaignOut,
    CampaignUpdateStatusRequest,
)
from app.services.security_service import write_audit

router = APIRouter(prefix="/admin/campaigns", tags=["admin.campaigns"])


@router.get("", response_model=CampaignListResponse)
def list_campaigns(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> CampaignListResponse:
    q = select(Campaign).where(Campaign.salon_id == ctx.salon_id)
    if status:
        q = q.where(Campaign.status == status)
    q = q.order_by(Campaign.id.desc())
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    rows = db.execute(q.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return CampaignListResponse(
        items=[CampaignOut.model_validate(x, from_attributes=True) for x in rows],
        page=page,
        page_size=page_size,
        total=int(total),
    )


@router.post("", response_model=CampaignOut)
def create_campaign(
    req: CampaignCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> CampaignOut:
    row = Campaign(
        salon_id=ctx.salon_id,
        title=req.title,
        channel=req.channel,
        audience_type=req.audience_type,
        message_text=req.message_text,
        scheduled_at=req.scheduled_at,
        status="active" if req.scheduled_at else "draft",
        created_at=int(time.time()),
    )
    db.add(row)
    db.flush()
    write_audit(db, salon_id=ctx.salon_id, actor_user_id=ctx.user_id, action="campaign.create", entity="campaign", entity_id=str(row.id))
    return CampaignOut.model_validate(row, from_attributes=True)


@router.put("/{campaign_id}/status", response_model=CampaignOut)
def update_campaign_status(
    campaign_id: int,
    req: CampaignUpdateStatusRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> CampaignOut:
    row = db.execute(
        select(Campaign).where(and_(Campaign.id == campaign_id, Campaign.salon_id == ctx.salon_id))
    ).scalar_one()
    row.status = req.status
    write_audit(db, salon_id=ctx.salon_id, actor_user_id=ctx.user_id, action="campaign.status", entity="campaign", entity_id=str(row.id), meta_json=req.status)
    return CampaignOut.model_validate(row, from_attributes=True)
