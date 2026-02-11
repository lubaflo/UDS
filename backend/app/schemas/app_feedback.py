from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class AppFeedbackCreateRequest(BaseModel):
    init_data: str
    feedback_type: str = Field(pattern="^(rating|complaint|suggestion)$")
    object_type: str = Field(default="service", pattern="^(service|product)$")
    object_id: int | None = Field(default=None, ge=1)
    rating: int | None = Field(default=None, ge=1, le=5)
    text: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def validate_payload(self) -> "AppFeedbackCreateRequest":
        if self.feedback_type == "rating" and self.rating is None:
            raise ValueError("rating is required for feedback_type=rating")
        return self


class AppMessageCreateRequest(BaseModel):
    init_data: str
    text: str = Field(min_length=1, max_length=4000)
    channel: str = Field(default="telegram", pattern="^(telegram|sms|email|vk|instagram|facebook|max)$")


class AppFeedbackCreateResponse(BaseModel):
    client_id: int
    feedback_id: int


class AppMessageCreateResponse(BaseModel):
    client_id: int
    message_id: int
