from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import Paginated


class OperationOut(BaseModel):
    id: int
    client_id: int
    op_type: str
    amount_rub: int
    discount_rub: int
    referral_discount_rub: int
    comment: str
    created_at: int


class OperationListResponse(Paginated):
    items: list[OperationOut]


class OperationCreateRequest(BaseModel):
    client_id: int
    op_type: str = Field(pattern="^(purchase|order|refund)$")
    amount_rub: int = Field(ge=0)
    discount_rub: int = Field(default=0, ge=0)
    referral_discount_rub: int = Field(default=0, ge=0)
    comment: str = Field(default="", max_length=1000)
