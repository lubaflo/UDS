from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import SecurityError, verify_telegram_init_data
from app.models import Salon
from app.schemas.appointments import AppAppointmentBookingRequest, AppAppointmentBookingResponse
from app.services.appointments_service import create_client_booking
from app.services.clients_service import get_or_create_client_by_tg_id

router = APIRouter(prefix="/app/appointments", tags=["app.appointments"])


def _resolve_salon_id(db: Session) -> int:
    salon = db.execute(select(Salon).limit(1)).scalar_one_or_none()
    if salon is None:
        raise HTTPException(status_code=400, detail="Salon not initialized")
    return salon.id


@router.post("/book", response_model=AppAppointmentBookingResponse)
def create_client_appointment(
    req: AppAppointmentBookingRequest,
    db: Session = Depends(get_db),
) -> AppAppointmentBookingResponse:
    try:
        tg_user = verify_telegram_init_data(req.init_data)
    except SecurityError as e:
        raise HTTPException(status_code=401, detail=str(e))

    salon_id = _resolve_salon_id(db)
    client = get_or_create_client_by_tg_id(
        db,
        salon_id=salon_id,
        tg_id=tg_user.tg_id,
        username=tg_user.username or "",
        full_name=f"{tg_user.first_name or ''} {tg_user.last_name or ''}".strip(),
    )

    row = create_client_booking(
        db,
        salon_id=salon_id,
        client_id=client.id,
        title=req.title,
        starts_at=req.starts_at,
    )
    return AppAppointmentBookingResponse(appointment_id=row.id, client_id=client.id, status=row.status)
