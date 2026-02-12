from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.schemas.employees import (
    EmployeeCategoryCreateRequest,
    EmployeeCategoryOut,
    EmployeeCreateRequest,
    EmployeeExportItem,
    EmployeeExportResponse,
    EmployeeHistoryOut,
    EmployeeListResponse,
    EmployeeOut,
    EmployeeUpdateRequest,
    PayrollOut,
    PayrollRunRequest,
    PayrollRunResponse,
    ScheduleCreateRequest,
    ScheduleOut,
    TimeEntryCreateRequest,
    TimeEntryListResponse,
    TimeEntryOut,
)
from app.services.employees_service import (
    create_category,
    create_employee,
    create_schedule,
    create_time_entry,
    delete_category,
    delete_employee,
    employee_to_dict,
    export_payroll,
    get_employee,
    list_categories,
    list_employees,
    list_history,
    list_schedule,
    list_time_entries,
    render_export_csv,
    run_payroll,
    update_employee,
)

router = APIRouter(prefix="/admin/employees", tags=["admin.employees"])


@router.get("/categories", response_model=list[EmployeeCategoryOut])
def get_categories(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> list[EmployeeCategoryOut]:
    rows = list_categories(db, salon_id=ctx.salon_id)
    return [EmployeeCategoryOut(id=x.id, name=x.name, is_active=x.is_active, created_at=x.created_at) for x in rows]


@router.post("/categories", response_model=EmployeeCategoryOut)
def post_category(
    req: EmployeeCategoryCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> EmployeeCategoryOut:
    row = create_category(db, salon_id=ctx.salon_id, name=req.name)
    return EmployeeCategoryOut(id=row.id, name=row.name, is_active=row.is_active, created_at=row.created_at)


@router.delete("/categories/{category_id}")
def remove_category(
    category_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    delete_category(db, salon_id=ctx.salon_id, category_id=category_id)
    return {"ok": True}


@router.get("", response_model=EmployeeListResponse)
def get_employees(
    q: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> EmployeeListResponse:
    items, total = list_employees(
        db,
        salon_id=ctx.salon_id,
        q=q,
        category_id=category_id,
        page=page,
        page_size=page_size,
    )
    return EmployeeListResponse(
        items=[EmployeeOut(**employee_to_dict(db, x)) for x in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("", response_model=EmployeeOut)
def post_employee(
    req: EmployeeCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> EmployeeOut:
    row = create_employee(
        db,
        salon_id=ctx.salon_id,
        full_name=req.full_name,
        category_id=req.category_id,
        position=req.position,
        email=req.email,
        phone=req.phone,
        payment_type=req.payment_type,
        hourly_rate=req.hourly_rate,
        piece_rate=req.piece_rate,
    )
    return EmployeeOut(**employee_to_dict(db, row))


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee_by_id(
    employee_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> EmployeeOut:
    row = get_employee(db, salon_id=ctx.salon_id, employee_id=employee_id)
    return EmployeeOut(**employee_to_dict(db, row))


@router.put("/{employee_id}", response_model=EmployeeOut)
def put_employee(
    employee_id: int,
    req: EmployeeUpdateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> EmployeeOut:
    row = update_employee(
        db,
        salon_id=ctx.salon_id,
        employee_id=employee_id,
        full_name=req.full_name,
        category_id=req.category_id,
        position=req.position,
        email=req.email,
        phone=req.phone,
        status=req.status,
        payment_type=req.payment_type,
        hourly_rate=req.hourly_rate,
        piece_rate=req.piece_rate,
    )
    return EmployeeOut(**employee_to_dict(db, row))


@router.delete("/{employee_id}")
def remove_employee(
    employee_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    delete_employee(db, salon_id=ctx.salon_id, employee_id=employee_id)
    return {"ok": True}


@router.post("/{employee_id}/timesheet", response_model=TimeEntryOut)
def post_timesheet(
    employee_id: int,
    req: TimeEntryCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> TimeEntryOut:
    row = create_time_entry(
        db,
        salon_id=ctx.salon_id,
        employee_id=employee_id,
        work_date=req.work_date,
        start_at=req.start_at,
        end_at=req.end_at,
        hours_worked=req.hours_worked,
        units_completed=req.units_completed,
        note=req.note,
    )
    return TimeEntryOut(
        id=row.id,
        work_date=row.work_date,
        start_at=row.start_at,
        end_at=row.end_at,
        hours_worked=float(row.hours_worked),
        units_completed=float(row.units_completed),
        note=row.note,
        created_at=row.created_at,
    )


@router.get("/{employee_id}/timesheet", response_model=TimeEntryListResponse)
def get_timesheet(
    employee_id: int,
    period_start: date | None = Query(default=None),
    period_end: date | None = Query(default=None),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> TimeEntryListResponse:
    rows = list_time_entries(
        db,
        salon_id=ctx.salon_id,
        employee_id=employee_id,
        period_start=period_start,
        period_end=period_end,
    )
    return TimeEntryListResponse(
        items=[
            TimeEntryOut(
                id=x.id,
                work_date=x.work_date,
                start_at=x.start_at,
                end_at=x.end_at,
                hours_worked=float(x.hours_worked),
                units_completed=float(x.units_completed),
                note=x.note,
                created_at=x.created_at,
            )
            for x in rows
        ],
        total_hours=round(sum(float(x.hours_worked) for x in rows), 2),
        total_units=round(sum(float(x.units_completed) for x in rows), 2),
    )


@router.post("/{employee_id}/schedule", response_model=ScheduleOut)
def post_schedule(
    employee_id: int,
    req: ScheduleCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ScheduleOut:
    row = create_schedule(
        db,
        salon_id=ctx.salon_id,
        employee_id=employee_id,
        work_date=req.work_date,
        planned_start=req.planned_start,
        planned_end=req.planned_end,
        break_minutes=req.break_minutes,
    )
    return ScheduleOut(
        id=row.id,
        work_date=row.work_date,
        planned_start=row.planned_start,
        planned_end=row.planned_end,
        break_minutes=row.break_minutes,
        status=row.status,
        created_at=row.created_at,
    )


@router.get("/{employee_id}/schedule", response_model=list[ScheduleOut])
def get_schedule(
    employee_id: int,
    period_start: date | None = Query(default=None),
    period_end: date | None = Query(default=None),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> list[ScheduleOut]:
    rows = list_schedule(
        db,
        salon_id=ctx.salon_id,
        employee_id=employee_id,
        period_start=period_start,
        period_end=period_end,
    )
    return [
        ScheduleOut(
            id=x.id,
            work_date=x.work_date,
            planned_start=x.planned_start,
            planned_end=x.planned_end,
            break_minutes=x.break_minutes,
            status=x.status,
            created_at=x.created_at,
        )
        for x in rows
    ]


@router.post("/payroll/run", response_model=PayrollRunResponse)
def post_run_payroll(
    req: PayrollRunRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> PayrollRunResponse:
    rows = run_payroll(
        db,
        salon_id=ctx.salon_id,
        period_start=req.period_start,
        period_end=req.period_end,
    )
    result = [
        PayrollOut(
            employee_id=x.employee_id,
            full_name=get_employee(db, salon_id=ctx.salon_id, employee_id=x.employee_id).full_name,
            payment_type=x.payment_type,
            hours=float(x.hours),
            units=float(x.units),
            amount=float(x.amount),
        )
        for x in rows
    ]
    return PayrollRunResponse(items=result, total_amount=round(sum(x.amount for x in result), 2))


@router.get("/{employee_id}/history", response_model=list[EmployeeHistoryOut])
def get_employee_history(
    employee_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> list[EmployeeHistoryOut]:
    rows = list_history(db, salon_id=ctx.salon_id, employee_id=employee_id)
    return [
        EmployeeHistoryOut(id=x.id, event_type=x.event_type, payload_json=x.payload_json, created_at=x.created_at)
        for x in rows
    ]


@router.get("/export", response_model=EmployeeExportResponse)
def get_export_json(
    full_name: str | None = Query(default=None),
    period_start: date = Query(...),
    period_end: date = Query(...),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> EmployeeExportResponse:
    rows = export_payroll(
        db,
        salon_id=ctx.salon_id,
        full_name=full_name,
        period_start=period_start,
        period_end=period_end,
    )
    items = [
        EmployeeExportItem(
            employee_id=employee.id,
            full_name=employee.full_name,
            period_start=accrual.period_start,
            period_end=accrual.period_end,
            payment_type=accrual.payment_type,
            hours=float(accrual.hours),
            units=float(accrual.units),
            amount=float(accrual.amount),
        )
        for employee, accrual in rows
    ]
    return EmployeeExportResponse(items=items, total_amount=round(sum(x.amount for x in items), 2))


@router.get("/export.csv", response_class=PlainTextResponse)
def get_export_csv(
    full_name: str | None = Query(default=None),
    period_start: date = Query(...),
    period_end: date = Query(...),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> PlainTextResponse:
    rows = export_payroll(
        db,
        salon_id=ctx.salon_id,
        full_name=full_name,
        period_start=period_start,
        period_end=period_end,
    )
    payload = render_export_csv(rows)
    return PlainTextResponse(
        content=payload,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employees_payroll_export.csv"},
    )
