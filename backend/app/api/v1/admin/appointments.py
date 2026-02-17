from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.schemas.appointments import (
    AdminAppointmentCreateRequest,
    AdminAppointmentOut,
    AdminAppointmentsListResponse,
    AdminAppointmentStatusUpdateRequest,
)
from app.services.appointments_service import (
    get_clients_map,
    get_employees_map,
    get_services_map,
    list_appointments,
    update_appointment_status,
)
from app.services.communications_service import create_appointment

router = APIRouter(prefix="/admin/appointments", tags=["admin.appointments"])


def _to_out(db: Session, *, salon_id: int, items) -> list[AdminAppointmentOut]:
    clients_map = get_clients_map(db, salon_id=salon_id, client_ids=[x.client_id for x in items])
    employees_map = get_employees_map(db, salon_id=salon_id, employee_ids=[x.employee_id for x in items if x.employee_id])
    services_map = get_services_map(db, salon_id=salon_id, service_ids=[x.service_id for x in items if x.service_id])
    out = []
    for x in items:
        client = clients_map.get(x.client_id)
        employee = employees_map.get(x.employee_id) if x.employee_id else None
        service = services_map.get(x.service_id) if x.service_id else None
        out.append(
            AdminAppointmentOut(
                id=x.id,
                client_id=x.client_id,
                client_name=client.full_name if client else "",
                employee_id=x.employee_id,
                employee_name=employee.full_name if employee else "",
                service_id=x.service_id,
                service_name=service.name if service else "",
                title=x.title,
                starts_at=x.starts_at,
                duration_minutes=x.duration_minutes,
                status=x.status,
                source=x.source,
            )
        )
    return out


@router.get("", response_model=AdminAppointmentsListResponse)
def get_admin_appointments(
    date_from: int | None = Query(default=None),
    date_to: int | None = Query(default=None),
    client_id: int | None = Query(default=None),
    employee_id: int | None = Query(default=None),
    service_id: int | None = Query(default=None),
    status: str | None = Query(default=None, pattern="^(scheduled|cancelled|completed)$"),
    source: str | None = Query(default=None, pattern="^(online|admin_phone|admin_manual)$"),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> AdminAppointmentsListResponse:
    items = list_appointments(
        db,
        salon_id=ctx.salon_id,
        date_from=date_from,
        date_to=date_to,
        client_id=client_id,
        employee_id=employee_id,
        service_id=service_id,
        status=status,
        source=source,
    )
    out = _to_out(db, salon_id=ctx.salon_id, items=items)
    return AdminAppointmentsListResponse(items=out, total=len(out))


@router.post("", response_model=AdminAppointmentOut)
def create_admin_appointment(
    req: AdminAppointmentCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> AdminAppointmentOut:
    row = create_appointment(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        client_id=req.client_id,
        employee_id=req.employee_id,
        service_id=req.service_id,
        title=req.title,
        starts_at=req.starts_at,
        duration_minutes=req.duration_minutes,
        source=req.source,
    )
    return _to_out(db, salon_id=ctx.salon_id, items=[row])[0]


@router.patch("/{appointment_id}/status", response_model=AdminAppointmentOut)
def patch_admin_appointment_status(
    appointment_id: int,
    req: AdminAppointmentStatusUpdateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> AdminAppointmentOut:
    row = update_appointment_status(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        appointment_id=appointment_id,
        status=req.status,
    )
    return _to_out(db, salon_id=ctx.salon_id, items=[row])[0]
