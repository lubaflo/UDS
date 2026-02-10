from __future__ import annotations

from pydantic import BaseModel


class DialogueItem(BaseModel):
    client_id: int
    client_name: str
    client_phone: str
    last_message_at: int
    last_message_text: str


class DialogueListResponse(BaseModel):
    items: list[DialogueItem]
    page: int
    page_size: int
    total: int


class MessageOut(BaseModel):
    id: int
    direction: str
    text: str
    created_at: int


class DialogueHistoryResponse(BaseModel):
    client_id: int
    items: list[MessageOut]


class SendMessageRequest(BaseModel):
    text: str