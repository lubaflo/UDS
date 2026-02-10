from __future__ import annotations

import time
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuditLog


def write_audit(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int | None,
    action: str,
    entity: str,
    entity_id: str = "",
    meta_json: str = "",
) -> None:
    row = AuditLog(
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        meta_json=meta_json,
        created_at=int(time.time()),
    )
    db.add(row)


def list_audit(db: Session, *, salon_id: int, page: int, page_size: int) -> tuple[list[AuditLog], int]:
    q = select(AuditLog).where(AuditLog.salon_id == salon_id).order_by(AuditLog.created_at.desc())
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    items = db.execute(q.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return items, int(total)