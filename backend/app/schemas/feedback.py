from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import Paginated


class FeedbackOut(BaseModel):
    id: int
    client_id: int | None
    feedback_type: str
    rating: int | None
    text: str
    status: str
    created_at: int


class FeedbackCreateRequest(BaseModel):
    client_id: int | None = None
    feedback_type: str = Field(pattern="^(rating|complaint|suggestion)$")
    rating: int | None = Field(default=None, ge=1, le=5)
    text: str = Field(default="", max_length=2000)


class FeedbackListResponse(Paginated):
    items: list[FeedbackOut]
