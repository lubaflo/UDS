from __future__ import annotations

from pydantic import BaseModel, Field


class TrafficChannelCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    channel_type: str = Field(default="custom", max_length=32)
    promo_code: str = Field(default="", max_length=64)


class TrafficChannelOut(BaseModel):
    id: int
    name: str
    channel_type: str
    promo_code: str
    clients_count: int
    buyers_count: int
    revenue_rub: int
    created_at: int


class TrafficChannelListResponse(BaseModel):
    items: list[TrafficChannelOut]
