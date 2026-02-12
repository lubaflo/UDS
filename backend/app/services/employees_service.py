from __future__ import annotations

import csv
import io
import json
import time
from datetime import date

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Employee,
    EmployeeCategory,
    EmployeeHistory,
    EmployeePayrollAccrual,
    EmployeeSchedule,
    EmployeeTimeEntry,
)


def _log_history(
    db: Session,
    *,
    salon_id: int,
    employee_id: int,
    event_type: str,
    payload: dict,
) -> None:
    db.add(
        EmployeeHistory(
            salon_id=salon_id,
            employee_id=employee_id,
            event_type=event_type,
            payload_json=json.dumps(payload, ensure_ascii=False),
            created_at=int(time.time()),
        )
    )


def _get_category(db: Session, *, salon_id: int, category_id: int) -> EmployeeCategory:
    category = db.execute(
        select(EmployeeCategory).where(EmployeeCategory.salon_id == salon_id, EmployeeCategory.id == category_id)
    ).scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


def get_employee(db: Session, *, salon_id: int, employee_id: int) -> Employee:
    employee = db.execute(
        select(Employee).where(Employee.salon_id == salon_id, Employee.id == employee_id)
    ).scalar_one_or_none()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


def create_category(db: Session, *, salon_id: int, name: str) -> EmployeeCategory:
    row = EmployeeCategory(salon_id=salon_id, name=name, is_active=True, created_at=int(time.time()))
    db.add(row)
    db.flush()
    return row


def list_categories(db: Session, *, salon_id: int) -> list[EmployeeCategory]:
    return db.execute(
        select(EmployeeCategory)
        .where(EmployeeCategory.salon_id == salon_id, EmployeeCategory.is_active.is_(True))
        .order_by(EmployeeCategory.name.asc())
    ).scalars().all()


def delete_category(db: Session, *, salon_id: int, category_id: int) -> None:
    category = _get_category(db, salon_id=salon_id, category_id=category_id)
    category.is_active = False


def create_employee(
    db: Session,
    *,
    salon_id: int,
    full_name: str,
    category_id: int | None,
    position: str,
    email: str,
    phone: str,
    payment_type: str,
    hourly_rate: float,
    piece_rate: float,
) -> Employee:
    if category_id is not None:
        _get_category(db, salon_id=salon_id, category_id=category_id)

    now = int(time.time())
    row = Employee(
        salon_id=salon_id,
        full_name=full_name,
        category_id=category_id,
        position=position,
        email=email,
        phone=phone,
        status="active",
        payment_type=payment_type,
        hourly_rate=hourly_rate,
        piece_rate=piece_rate,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()
    _log_history(
        db,
        salon_id=salon_id,
        employee_id=row.id,
        event_type="employee.created",
        payload={"full_name": full_name, "payment_type": payment_type},
    )
    return row


def update_employee(
    db: Session,
    *,
    salon_id: int,
    employee_id: int,
    full_name: str | None,
    category_id: int | None,
    position: str | None,
    email: str | None,
    phone: str | None,
    status: str | None,
    payment_type: str | None,
    hourly_rate: float | None,
    piece_rate: float | None,
) -> Employee:
    row = get_employee(db, salon_id=salon_id, employee_id=employee_id)
    if category_id is not None:
        _get_category(db, salon_id=salon_id, category_id=category_id)

    changed: dict[str, str | float | int | None] = {}
    updates = {
        "full_name": full_name,
        "category_id": category_id,
        "position": position,
        "email": email,
        "phone": phone,
        "status": status,
        "payment_type": payment_type,
        "hourly_rate": hourly_rate,
        "piece_rate": piece_rate,
    }
    for field, value in updates.items():
        if value is not None and value != getattr(row, field):
            setattr(row, field, value)
            changed[field] = value

    if changed:
        row.updated_at = int(time.time())
        _log_history(
            db,
            salon_id=salon_id,
            employee_id=row.id,
            event_type="employee.updated",
            payload=changed,
        )
    return row


def list_employees(
    db: Session,
    *,
    salon_id: int,
    q: str | None,
    category_id: int | None,
    page: int,
    page_size: int,
) -> tuple[list[Employee], int]:
    stmt = select(Employee).where(Employee.salon_id == salon_id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Employee.full_name.ilike(like),
                Employee.position.ilike(like),
                Employee.email.ilike(like),
                Employee.phone.ilike(like),
            )
        )
    if category_id is not None:
        stmt = stmt.where(Employee.category_id == category_id)

    stmt = stmt.order_by(Employee.id.desc())
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return items, int(total)


def delete_employee(db: Session, *, salon_id: int, employee_id: int) -> None:
    row = get_employee(db, salon_id=salon_id, employee_id=employee_id)
    row.status = "archived"
    row.updated_at = int(time.time())
    _log_history(
        db,
        salon_id=salon_id,
        employee_id=row.id,
        event_type="employee.archived",
        payload={"status": "archived"},
    )


def create_time_entry(
    db: Session,
    *,
    salon_id: int,
    employee_id: int,
    work_date: date,
    start_at: str,
    end_at: str,
    hours_worked: float,
    units_completed: float,
    note: str,
) -> EmployeeTimeEntry:
    get_employee(db, salon_id=salon_id, employee_id=employee_id)
    row = EmployeeTimeEntry(
        salon_id=salon_id,
        employee_id=employee_id,
        work_date=work_date,
        start_at=start_at,
        end_at=end_at,
        hours_worked=hours_worked,
        units_completed=units_completed,
        note=note,
        created_at=int(time.time()),
    )
    db.add(row)
    db.flush()
    _log_history(
        db,
        salon_id=salon_id,
        employee_id=employee_id,
        event_type="timesheet.logged",
        payload={"date": work_date.isoformat(), "hours": hours_worked, "units": units_completed},
    )
    return row


def list_time_entries(
    db: Session,
    *,
    salon_id: int,
    employee_id: int,
    period_start: date | None,
    period_end: date | None,
) -> list[EmployeeTimeEntry]:
    get_employee(db, salon_id=salon_id, employee_id=employee_id)
    stmt = select(EmployeeTimeEntry).where(
        EmployeeTimeEntry.salon_id == salon_id,
        EmployeeTimeEntry.employee_id == employee_id,
    )
    if period_start is not None:
        stmt = stmt.where(EmployeeTimeEntry.work_date >= period_start)
    if period_end is not None:
        stmt = stmt.where(EmployeeTimeEntry.work_date <= period_end)
    return db.execute(stmt.order_by(EmployeeTimeEntry.work_date.desc())).scalars().all()


def create_schedule(
    db: Session,
    *,
    salon_id: int,
    employee_id: int,
    work_date: date,
    planned_start: str,
    planned_end: str,
    break_minutes: int,
) -> EmployeeSchedule:
    get_employee(db, salon_id=salon_id, employee_id=employee_id)
    row = EmployeeSchedule(
        salon_id=salon_id,
        employee_id=employee_id,
        work_date=work_date,
        planned_start=planned_start,
        planned_end=planned_end,
        break_minutes=break_minutes,
        status="planned",
        created_at=int(time.time()),
    )
    db.add(row)
    db.flush()
    _log_history(
        db,
        salon_id=salon_id,
        employee_id=employee_id,
        event_type="schedule.planned",
        payload={"date": work_date.isoformat(), "from": planned_start, "to": planned_end},
    )
    return row


def list_schedule(
    db: Session,
    *,
    salon_id: int,
    employee_id: int,
    period_start: date | None,
    period_end: date | None,
) -> list[EmployeeSchedule]:
    get_employee(db, salon_id=salon_id, employee_id=employee_id)
    stmt = select(EmployeeSchedule).where(
        EmployeeSchedule.salon_id == salon_id,
        EmployeeSchedule.employee_id == employee_id,
    )
    if period_start is not None:
        stmt = stmt.where(EmployeeSchedule.work_date >= period_start)
    if period_end is not None:
        stmt = stmt.where(EmployeeSchedule.work_date <= period_end)
    return db.execute(stmt.order_by(EmployeeSchedule.work_date.asc())).scalars().all()


def run_payroll(
    db: Session,
    *,
    salon_id: int,
    period_start: date,
    period_end: date,
) -> list[EmployeePayrollAccrual]:
    employees = db.execute(
        select(Employee).where(Employee.salon_id == salon_id, Employee.status == "active")
    ).scalars().all()

    rows: list[EmployeePayrollAccrual] = []
    now = int(time.time())
    for employee in employees:
        entries = db.execute(
            select(EmployeeTimeEntry).where(
                EmployeeTimeEntry.salon_id == salon_id,
                EmployeeTimeEntry.employee_id == employee.id,
                EmployeeTimeEntry.work_date >= period_start,
                EmployeeTimeEntry.work_date <= period_end,
            )
        ).scalars().all()

        total_hours = float(sum(x.hours_worked for x in entries))
        total_units = float(sum(x.units_completed for x in entries))
        if employee.payment_type == "piecework":
            amount = total_units * float(employee.piece_rate)
        else:
            amount = total_hours * float(employee.hourly_rate)

        accrual = EmployeePayrollAccrual(
            salon_id=salon_id,
            employee_id=employee.id,
            period_start=period_start,
            period_end=period_end,
            payment_type=employee.payment_type,
            hours=round(total_hours, 2),
            units=round(total_units, 2),
            amount=round(amount, 2),
            status="calculated",
            created_at=now,
        )
        db.add(accrual)
        rows.append(accrual)

        _log_history(
            db,
            salon_id=salon_id,
            employee_id=employee.id,
            event_type="payroll.calculated",
            payload={
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "amount": round(amount, 2),
            },
        )

    db.flush()
    return rows


def list_history(db: Session, *, salon_id: int, employee_id: int) -> list[EmployeeHistory]:
    get_employee(db, salon_id=salon_id, employee_id=employee_id)
    return db.execute(
        select(EmployeeHistory)
        .where(EmployeeHistory.salon_id == salon_id, EmployeeHistory.employee_id == employee_id)
        .order_by(EmployeeHistory.created_at.desc())
    ).scalars().all()


def employee_to_dict(db: Session, row: Employee) -> dict:
    category_name = None
    if row.category_id:
        category_name = db.execute(
            select(EmployeeCategory.name).where(
                EmployeeCategory.salon_id == row.salon_id,
                EmployeeCategory.id == row.category_id,
            )
        ).scalar_one_or_none()
    return {
        "id": row.id,
        "full_name": row.full_name,
        "category_id": row.category_id,
        "category_name": category_name,
        "position": row.position,
        "email": row.email,
        "phone": row.phone,
        "status": row.status,
        "payment_type": row.payment_type,
        "hourly_rate": float(row.hourly_rate),
        "piece_rate": float(row.piece_rate),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def export_payroll(
    db: Session,
    *,
    salon_id: int,
    full_name: str | None,
    period_start: date,
    period_end: date,
) -> list[tuple[Employee, EmployeePayrollAccrual]]:
    stmt = (
        select(Employee, EmployeePayrollAccrual)
        .join(EmployeePayrollAccrual, EmployeePayrollAccrual.employee_id == Employee.id)
        .where(
            Employee.salon_id == salon_id,
            EmployeePayrollAccrual.salon_id == salon_id,
            EmployeePayrollAccrual.period_start >= period_start,
            EmployeePayrollAccrual.period_end <= period_end,
        )
        .order_by(Employee.full_name.asc(), EmployeePayrollAccrual.created_at.desc())
    )
    if full_name:
        stmt = stmt.where(Employee.full_name.ilike(f"%{full_name.strip()}%"))
    return db.execute(stmt).all()


def render_export_csv(rows: list[tuple[Employee, EmployeePayrollAccrual]]) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["employee_id", "full_name", "period_start", "period_end", "payment_type", "hours", "units", "amount"])
    for employee, accrual in rows:
        writer.writerow(
            [
                employee.id,
                employee.full_name,
                accrual.period_start.isoformat(),
                accrual.period_end.isoformat(),
                accrual.payment_type,
                f"{accrual.hours:.2f}",
                f"{accrual.units:.2f}",
                f"{accrual.amount:.2f}",
            ]
        )
    return out.getvalue()
