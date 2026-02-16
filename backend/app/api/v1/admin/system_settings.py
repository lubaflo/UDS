from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import SystemSettings
from app.schemas.system_settings import SystemSettingsOut, SystemSettingsUpdateRequest
from app.services.security_service import write_audit

router = APIRouter(prefix="/admin/system-settings", tags=["admin.system_settings"])


def _get_or_create_settings(db: Session, salon_id: int) -> SystemSettings:
    row = db.execute(select(SystemSettings).where(SystemSettings.salon_id == salon_id)).scalar_one_or_none()
    if row is None:
        row = SystemSettings(salon_id=salon_id)
        db.add(row)
        db.flush()
    return row


@router.get("", response_model=SystemSettingsOut)
def get_system_settings(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> SystemSettingsOut:
    row = _get_or_create_settings(db, ctx.salon_id)
    return SystemSettingsOut(
        weekly_report_enabled=row.weekly_report_enabled,
        global_search_enabled=row.global_search_enabled,
        responsible_first_name=row.responsible_first_name,
        responsible_last_name=row.responsible_last_name,
        responsible_phone=row.responsible_phone,
        avg_purchases_per_day=row.avg_purchases_per_day,
    )


@router.put("", response_model=SystemSettingsOut)
def update_system_settings(
    req: SystemSettingsUpdateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> SystemSettingsOut:
    row = _get_or_create_settings(db, ctx.salon_id)
    row.weekly_report_enabled = req.weekly_report_enabled
    row.global_search_enabled = req.global_search_enabled
    row.responsible_first_name = req.responsible_first_name
    row.responsible_last_name = req.responsible_last_name
    row.responsible_phone = req.responsible_phone
    row.avg_purchases_per_day = req.avg_purchases_per_day

    write_audit(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        action="system_settings.update",
        entity="system_settings",
        entity_id=str(row.id),
    )

    return SystemSettingsOut(
        weekly_report_enabled=row.weekly_report_enabled,
        global_search_enabled=row.global_search_enabled,
        responsible_first_name=row.responsible_first_name,
        responsible_last_name=row.responsible_last_name,
        responsible_phone=row.responsible_phone,
        avg_purchases_per_day=row.avg_purchases_per_day,
    )
