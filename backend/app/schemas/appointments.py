from __future__ import annotations

from pydantic import BaseModel, Field


class BookingFlowStep(BaseModel):
    code: str
    title: str


class BookingMasterOption(BaseModel):
    id: int
    full_name: str
    position: str


class BookingServiceOption(BaseModel):
    id: int
    name: str
    duration_minutes: int
    price_rub: int


class BookingOptionsResponse(BaseModel):
    mode: str
    steps: list[BookingFlowStep]
    masters: list[BookingMasterOption]
    services: list[BookingServiceOption]


class BookingSlotOut(BaseModel):
    starts_at: int
    label: str


class BookingSlotsResponse(BaseModel):
    items: list[BookingSlotOut]


class AdminAppointmentCreateRequest(BaseModel):
    client_id: int
    employee_id: int | None = None
    service_id: int | None = None
    title: str = Field(default="Процедура", max_length=200)
    starts_at: int
    duration_minutes: int = Field(default=60, ge=5, le=8 * 60)
    source: str = Field(default="admin_manual", pattern="^(online|admin_phone|admin_manual)$")


class AdminAppointmentStatusUpdateRequest(BaseModel):
    status: str = Field(pattern="^(scheduled|cancelled|completed)$")


class AdminAppointmentOut(BaseModel):
    id: int
    client_id: int
    client_name: str
    employee_id: int | None
    employee_name: str
    service_id: int | None
    service_name: str
    title: str
    starts_at: int
    duration_minutes: int
    status: str
    source: str


class AdminAppointmentsListResponse(BaseModel):
    items: list[AdminAppointmentOut]
    total: int


class AppAppointmentBookingRequest(BaseModel):
    init_data: str = Field(min_length=10)
    employee_id: int | None = None
    service_id: int | None = None
    title: str = Field(default="Онлайн-запись", max_length=200)
    starts_at: int
    duration_minutes: int = Field(default=60, ge=5, le=8 * 60)


class AppAppointmentBookingResponse(BaseModel):
    appointment_id: int
    client_id: int
    status: str
