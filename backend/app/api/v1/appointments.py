from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import SecurityError, verify_telegram_init_data
from app.models import Appointment, Employee, Product, Salon
from app.schemas.appointments import (
    AppAppointmentBookingRequest,
    AppAppointmentBookingResponse,
    BookingFlowStep,
    BookingMasterOption,
    BookingOptionsResponse,
    BookingServiceOption,
    BookingSlotOut,
    BookingSlotsResponse,
)
from app.services.appointments_service import create_client_booking
from app.services.clients_service import get_or_create_client_by_tg_id

router = APIRouter(prefix="/app/appointments", tags=["app.appointments"])


def _resolve_salon_id(db: Session) -> int:
    salon = db.execute(select(Salon).limit(1)).scalar_one_or_none()
    if salon is None:
        raise HTTPException(status_code=400, detail="Salon not initialized")
    return salon.id


@router.get("/booking-options", response_model=BookingOptionsResponse)
def get_booking_options(db: Session = Depends(get_db)) -> BookingOptionsResponse:
    salon_id = _resolve_salon_id(db)
    masters = db.execute(
        select(Employee).where(and_(Employee.salon_id == salon_id, Employee.status == "active")).order_by(Employee.full_name)
    ).scalars().all()
    services = db.execute(
        select(Product).where(and_(Product.salon_id == salon_id, Product.item_type == "service")).order_by(Product.name)
    ).scalars().all()

    return BookingOptionsResponse(
        mode="menu",
        steps=[
            BookingFlowStep(code="employee", title="Выбор мастера"),
            BookingFlowStep(code="service", title="Выбор услуги"),
            BookingFlowStep(code="date", title="Выбор даты"),
            BookingFlowStep(code="time", title="Выбор времени"),
        ],
        masters=[BookingMasterOption(id=m.id, full_name=m.full_name, position=m.position) for m in masters],
        services=[
            BookingServiceOption(id=s.id, name=s.name, duration_minutes=60, price_rub=s.price_rub)
            for s in services
        ],
    )


@router.get("/slots", response_model=BookingSlotsResponse)
def get_booking_slots(
    date_ts: int = Query(..., description="Unix timestamp начала дня"),
    employee_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> BookingSlotsResponse:
    salon_id = _resolve_salon_id(db)
    day_start = date_ts
    day_end = day_start + 24 * 60 * 60

    q = select(Appointment).where(
        and_(
            Appointment.salon_id == salon_id,
            Appointment.starts_at >= day_start,
            Appointment.starts_at < day_end,
            Appointment.status == "scheduled",
        )
    )
    if employee_id is not None:
        q = q.where(Appointment.employee_id == employee_id)
    busy = db.execute(q).scalars().all()
    busy_starts = {x.starts_at for x in busy}

    slots: list[BookingSlotOut] = []
    for hour in range(9, 21):
        starts_at = day_start + hour * 3600
        if starts_at in busy_starts:
            continue
        dt = datetime.fromtimestamp(starts_at, tz=timezone.utc)
        slots.append(BookingSlotOut(starts_at=starts_at, label=dt.strftime("%H:%M")))

    return BookingSlotsResponse(items=slots)


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
        employee_id=req.employee_id,
        service_id=req.service_id,
        title=req.title,
        starts_at=req.starts_at,
        duration_minutes=req.duration_minutes,
    )
    return AppAppointmentBookingResponse(appointment_id=row.id, client_id=client.id, status=row.status)
