from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import Paginated


class CertificateOut(BaseModel):
    id: int
    client_id: int | None
    title: str
    amount_rub: int
    issue_method: str
    status: str
    expires_at: int | None
    created_at: int


class CertificateCreateRequest(BaseModel):
    client_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    amount_rub: int = Field(gt=0)
    issue_method: str = Field(
        pattern="^(automatic|birthday|cross_marketing|link|manual)$"
    )
    expires_at: int | None = None


class CertificateListResponse(Paginated):
    items: list[CertificateOut]
