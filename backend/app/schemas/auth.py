from __future__ import annotations

from pydantic import BaseModel


class VerifyInitDataRequest(BaseModel):
    init_data: str


class VerifyInitDataResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"