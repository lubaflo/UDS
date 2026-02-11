from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import Certificate
from app.schemas.certificates import CertificateCreateRequest, CertificateListResponse, CertificateOut
from app.services.security_service import write_audit

router = APIRouter(prefix="/admin/certificates", tags=["admin.certificates"])


@router.get("", response_model=CertificateListResponse)
def list_certificates(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> CertificateListResponse:
    q = select(Certificate).where(Certificate.salon_id == ctx.salon_id)
    if status:
        q = q.where(Certificate.status == status)
    q = q.order_by(Certificate.created_at.desc())

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    rows = db.execute(q.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return CertificateListResponse(
        items=[CertificateOut.model_validate(x, from_attributes=True) for x in rows],
        page=page,
        page_size=page_size,
        total=int(total),
    )


@router.post("", response_model=CertificateOut)
def create_certificate(
    req: CertificateCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> CertificateOut:
    row = Certificate(
        salon_id=ctx.salon_id,
        client_id=req.client_id,
        title=req.title,
        amount_rub=req.amount_rub,
        issue_method=req.issue_method,
        status="in_progress",
        expires_at=req.expires_at,
        created_at=int(time.time()),
    )
    db.add(row)
    db.flush()
    write_audit(db, salon_id=ctx.salon_id, actor_user_id=ctx.user_id, action="certificate.create", entity="certificate", entity_id=str(row.id))
    return CertificateOut.model_validate(row, from_attributes=True)
