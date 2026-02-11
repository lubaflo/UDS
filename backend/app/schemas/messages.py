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
    message_type: str
    group_name: str
    channel: str
    delivery_status: str
    scheduled_for: int | None
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
    delivery_status: str = Field(default="sent", pattern="^(pending|sent|delivered|failed|read)$")
    scheduled_for: int | None = Field(default=None, ge=0)


class GroupSendMessageRequest(BaseModel):
    client_ids: list[int] = Field(min_length=1)
    group_name: str = Field(min_length=1, max_length=100)
    channel: str = Field(pattern="^(telegram|sms|email|vk|instagram|facebook|max)$")
    text: str = Field(min_length=1, max_length=4000)
    subject: str = Field(default="", max_length=200)
    delivery_status: str = Field(default="pending", pattern="^(pending|sent|delivered|failed|read)$")
    scheduled_for: int | None = Field(default=None, ge=0)


class GroupSendMessageResponse(BaseModel):
    group_name: str
    sent_count: int
    items: list[MessageOut]


class MessageRegistryItem(BaseModel):
    message_id: int
    client_id: int
    client_name: str
    channel: str
    delivery_status: str
    message_type: str
    group_name: str
    text: str
    created_at: int
    scheduled_for: int | None


class MessageRegistryResponse(BaseModel):
    items: list[MessageRegistryItem]
    page: int
    page_size: int
    total: int
