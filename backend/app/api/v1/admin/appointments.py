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
    list_appointments,
    update_appointment_status,
)
from app.services.communications_service import create_appointment

router = APIRouter(prefix="/admin/appointments", tags=["admin.appointments"])


@router.get("", response_model=AdminAppointmentsListResponse)
def get_admin_appointments(
    date_from: int | None = Query(default=None),
    date_to: int | None = Query(default=None),
    client_id: int | None = Query(default=None),
    status: str | None = Query(default=None, pattern="^(scheduled|cancelled|completed)$"),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> AdminAppointmentsListResponse:
    items = list_appointments(
        db,
        salon_id=ctx.salon_id,
        date_from=date_from,
        date_to=date_to,
        client_id=client_id,
        status=status,
    )
    clients_map = get_clients_map(db, salon_id=ctx.salon_id, client_ids=[x.client_id for x in items])
    out = [
        AdminAppointmentOut(
            id=x.id,
            client_id=x.client_id,
            client_name=(clients_map.get(x.client_id).full_name if clients_map.get(x.client_id) else ""),
            title=x.title,
            starts_at=x.starts_at,
            status=x.status,
        )
        for x in items
    ]
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
        title=req.title,
        starts_at=req.starts_at,
    )
    clients_map = get_clients_map(db, salon_id=ctx.salon_id, client_ids=[row.client_id])
    client_name = clients_map.get(row.client_id).full_name if clients_map.get(row.client_id) else ""
    return AdminAppointmentOut(
        id=row.id,
        client_id=row.client_id,
        client_name=client_name,
        title=row.title,
        starts_at=row.starts_at,
        status=row.status,
    )


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
    clients_map = get_clients_map(db, salon_id=ctx.salon_id, client_ids=[row.client_id])
    client_name = clients_map.get(row.client_id).full_name if clients_map.get(row.client_id) else ""
    return AdminAppointmentOut(
        id=row.id,
        client_id=row.client_id,
        client_name=client_name,
        title=row.title,
        starts_at=row.starts_at,
        status=row.status,
    )
