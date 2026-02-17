from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models import Appointment, Client, Employee, Product
from app.services.communications_service import create_appointment
from app.services.security_service import write_audit


def list_appointments(
    db: Session,
    *,
    salon_id: int,
    date_from: int | None,
    date_to: int | None,
    client_id: int | None,
    employee_id: int | None,
    service_id: int | None,
    status: str | None,
    source: str | None,
) -> list[Appointment]:
    q = select(Appointment).where(Appointment.salon_id == salon_id)
    if date_from is not None:
        q = q.where(Appointment.starts_at >= date_from)
    if date_to is not None:
        q = q.where(Appointment.starts_at <= date_to)
    if client_id is not None:
        q = q.where(Appointment.client_id == client_id)
    if employee_id is not None:
        q = q.where(Appointment.employee_id == employee_id)
    if service_id is not None:
        q = q.where(Appointment.service_id == service_id)
    if status is not None:
        q = q.where(Appointment.status == status)
    if source is not None:
        q = q.where(Appointment.source == source)
    return db.execute(q.order_by(Appointment.starts_at.asc(), Appointment.id.asc())).scalars().all()


def update_appointment_status(
    db: Session,
    *,
    salon_id: int,
    actor_user_id: int,
    appointment_id: int,
    status: str,
) -> Appointment:
    row = db.execute(
        select(Appointment).where(
            and_(
                Appointment.id == appointment_id,
                Appointment.salon_id == salon_id,
            )
        )
    ).scalar_one()
    row.status = status
    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=actor_user_id,
        action="appointment.status.update",
        entity="appointment",
        entity_id=str(appointment_id),
        meta_json=f"status={status}",
    )
    return row


def create_client_booking(
    db: Session,
    *,
    salon_id: int,
    client_id: int,
    employee_id: int | None,
    service_id: int | None,
    title: str,
    starts_at: int,
    duration_minutes: int,
) -> Appointment:
    appointment = create_appointment(
        db,
        salon_id=salon_id,
        actor_user_id=0,
        client_id=client_id,
        employee_id=employee_id,
        service_id=service_id,
        title=title,
        starts_at=starts_at,
        duration_minutes=duration_minutes,
        source="online",
    )
    write_audit(
        db,
        salon_id=salon_id,
        actor_user_id=None,
        action="appointment.client.book",
        entity="appointment",
        entity_id=str(appointment.id),
        meta_json=f"client_id={client_id}",
    )
    return appointment


def get_clients_map(db: Session, *, salon_id: int, client_ids: list[int]) -> dict[int, Client]:
    if not client_ids:
        return {}
    clients = db.execute(
        select(Client).where(
            and_(
                Client.salon_id == salon_id,
                Client.id.in_(client_ids),
            )
        )
    ).scalars().all()
    return {client.id: client for client in clients}


def get_employees_map(db: Session, *, salon_id: int, employee_ids: list[int]) -> dict[int, Employee]:
    employee_ids = [x for x in employee_ids if x is not None]
    if not employee_ids:
        return {}
    rows = db.execute(
        select(Employee).where(
            and_(
                Employee.salon_id == salon_id,
                Employee.id.in_(employee_ids),
            )
        )
    ).scalars().all()
    return {row.id: row for row in rows}


def get_services_map(db: Session, *, salon_id: int, service_ids: list[int]) -> dict[int, Product]:
    service_ids = [x for x in service_ids if x is not None]
    if not service_ids:
        return {}
    rows = db.execute(
        select(Product).where(
            and_(
                Product.salon_id == salon_id,
                Product.id.in_(service_ids),
            )
        )
    ).scalars().all()
    return {row.id: row for row in rows}
