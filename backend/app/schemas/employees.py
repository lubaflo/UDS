from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class EmployeeCategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class EmployeeCategoryOut(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: int


class EmployeeCreateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    category_id: int | None = None
    position: str = Field(default="", max_length=120)
    email: str = Field(default="", max_length=254)
    phone: str = Field(default="", max_length=32)
    payment_type: str = Field(default="hourly", pattern="^(hourly|piecework)$")
    hourly_rate: float = Field(default=0, ge=0)
    piece_rate: float = Field(default=0, ge=0)


class EmployeeUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    category_id: int | None = None
    position: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, pattern="^(active|dismissed|archived)$")
    payment_type: str | None = Field(default=None, pattern="^(hourly|piecework)$")
    hourly_rate: float | None = Field(default=None, ge=0)
    piece_rate: float | None = Field(default=None, ge=0)


class EmployeeOut(BaseModel):
    id: int
    full_name: str
    category_id: int | None
    category_name: str | None
    position: str
    email: str
    phone: str
    status: str
    payment_type: str
    hourly_rate: float
    piece_rate: float
    created_at: int
    updated_at: int


class EmployeeListResponse(BaseModel):
    items: list[EmployeeOut]
    page: int
    page_size: int
    total: int


class TimeEntryCreateRequest(BaseModel):
    work_date: date
    start_at: str = Field(default="", pattern=r"^$|^([01]\d|2[0-3]):[0-5]\d$")
    end_at: str = Field(default="", pattern=r"^$|^([01]\d|2[0-3]):[0-5]\d$")
    hours_worked: float = Field(default=0, ge=0)
    units_completed: float = Field(default=0, ge=0)
    note: str = Field(default="", max_length=1000)


class TimeEntryOut(BaseModel):
    id: int
    work_date: date
    start_at: str
    end_at: str
    hours_worked: float
    units_completed: float
    note: str
    created_at: int


class TimeEntryListResponse(BaseModel):
    items: list[TimeEntryOut]
    total_hours: float
    total_units: float


class ScheduleCreateRequest(BaseModel):
    work_date: date
    planned_start: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    planned_end: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    break_minutes: int = Field(default=0, ge=0, le=600)


class ScheduleOut(BaseModel):
    id: int
    work_date: date
    planned_start: str
    planned_end: str
    break_minutes: int
    status: str
    created_at: int


class PayrollRunRequest(BaseModel):
    period_start: date
    period_end: date


class PayrollOut(BaseModel):
    employee_id: int
    full_name: str
    payment_type: str
    hours: float
    units: float
    amount: float


class PayrollRunResponse(BaseModel):
    items: list[PayrollOut]
    total_amount: float


class EmployeeHistoryOut(BaseModel):
    id: int
    event_type: str
    payload_json: str
    created_at: int


class EmployeeExportItem(BaseModel):
    employee_id: int
    full_name: str
    period_start: date
    period_end: date
    payment_type: str
    hours: float
    units: float
    amount: float


class EmployeeExportResponse(BaseModel):
    items: list[EmployeeExportItem]
    total_amount: float
