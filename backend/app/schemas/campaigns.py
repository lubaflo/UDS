from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import Paginated


class CampaignOut(BaseModel):
    id: int
    title: str
    channel: str
    audience_type: str
    message_text: str
    scheduled_at: int | None
    status: str
    created_at: int


class CampaignCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    channel: str = Field(default="telegram", pattern="^(telegram|uds_app)$")
    audience_type: str = Field(default="all", pattern="^(all|new|active|inactive|segment)$")
    message_text: str = Field(min_length=1, max_length=4000)
    scheduled_at: int | None = None


class CampaignUpdateStatusRequest(BaseModel):
    status: str = Field(pattern="^(draft|active|archived|sent)$")


class CampaignListResponse(Paginated):
    items: list[CampaignOut]
