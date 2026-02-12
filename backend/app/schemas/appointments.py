from __future__ import annotations

from pydantic import BaseModel, Field


class AdminAppointmentCreateRequest(BaseModel):
    client_id: int
    title: str = Field(default="Процедура", max_length=200)
    starts_at: int


class AdminAppointmentStatusUpdateRequest(BaseModel):
    status: str = Field(pattern="^(scheduled|cancelled|completed)$")


class AdminAppointmentOut(BaseModel):
    id: int
    client_id: int
    client_name: str
    title: str
    starts_at: int
    status: str


class AdminAppointmentsListResponse(BaseModel):
    items: list[AdminAppointmentOut]
    total: int


class AppAppointmentBookingRequest(BaseModel):
    init_data: str = Field(min_length=10)
    title: str = Field(default="Онлайн-запись", max_length=200)
    starts_at: int


class AppAppointmentBookingResponse(BaseModel):
    appointment_id: int
    client_id: int
    status: str

