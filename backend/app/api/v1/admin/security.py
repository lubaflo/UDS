from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.schemas.security import AuditLogListResponse, AuditLogOut
from app.services.security_service import list_audit

router = APIRouter(prefix="/admin/audit-log", tags=["admin.security"])


@router.get("", response_model=AuditLogListResponse)
def get_audit(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    items, total = list_audit(db, salon_id=ctx.salon_id, page=page, page_size=page_size)
    out = [
        AuditLogOut(
            id=x.id,
            action=x.action,
            entity=x.entity,
            entity_id=x.entity_id,
            actor_user_id=x.actor_user_id,
            meta_json=x.meta_json,
            created_at=x.created_at,
        )
        for x in items
    ]
    return AuditLogListResponse(items=out, page=page, page_size=page_size, total=total)