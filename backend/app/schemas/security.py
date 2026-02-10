from __future__ import annotations

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    action: str
    entity: str
    entity_id: str
    actor_user_id: int | None
    meta_json: str
    created_at: int


class AuditLogListResponse(BaseModel):
    items: list[AuditLogOut]
    page: int
    page_size: int
    total: int