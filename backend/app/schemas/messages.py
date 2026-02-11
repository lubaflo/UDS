from __future__ import annotations

from pydantic import BaseModel, Field


class DialogueItem(BaseModel):
    client_id: int
    client_tg_id: int | None
    client_name: str
    client_phone: str
    last_message_at: int
    last_message_text: str
    last_message_channel: str


class DialogueListResponse(BaseModel):
    items: list[DialogueItem]
    page: int
    page_size: int
    total: int


class MessageOut(BaseModel):
    id: int
    direction: str
    channel: str
    text: str
    subject: str
    destination: str
    created_at: int


class DialogueHistoryResponse(BaseModel):
    client_id: int
    client_tg_id: int | None
    items: list[MessageOut]


class SendMessageRequest(BaseModel):
    channel: str = Field(pattern="^(telegram|sms|email|vk|instagram|facebook|max)$")
    text: str = Field(min_length=1, max_length=4000)
    subject: str = Field(default="", max_length=200)
