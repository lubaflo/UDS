from __future__ import annotations

from pydantic import BaseModel, Field


class ClientOut(BaseModel):
    id: int
    name: str
    phone: str
    status: str
    tags: list[str] = Field(default_factory=list)
    notes: str
    visits_count: int
    total_spent_rub: int
    last_visit_at: str


class ClientListResponse(BaseModel):
    items: list[ClientOut]
    page: int
    page_size: int
    total: int


class ClientUpdateRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    status: str | None = None
    notes: str | None = None


class ClientTagsRequest(BaseModel):
    tags: list[str]