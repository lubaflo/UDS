from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import Paginated


NEWS_EVENT_PATTERN = "^(view|transition|click|booking|purchase|add_to_cart)$"


class NewsPostCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=3000)
    cover_image_url: str = Field(default="", max_length=512)
    status: str = Field(default="active", pattern="^(active|archived|draft)$")


class NewsPostUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, min_length=1, max_length=3000)
    cover_image_url: str | None = Field(default=None, max_length=512)
    status: str | None = Field(default=None, pattern="^(active|archived|draft)$")


class NewsPostOut(BaseModel):
    id: int
    title: str
    body: str
    cover_image_url: str
    status: str
    created_at: int
    updated_at: int


class NewsListResponse(Paginated):
    items: list[NewsPostOut]


class NewsTrackRequest(BaseModel):
    news_post_id: int
    event_type: str = Field(pattern=NEWS_EVENT_PATTERN)
    client_id: int | None = None
    source: str = Field(default="", max_length=64)
    occurred_at: int | None = None


class NewsMetricOut(BaseModel):
    event_type: str
    count: int


class NewsStatsOut(BaseModel):
    news_post_id: int
    total_events: int
    metrics: list[NewsMetricOut]
